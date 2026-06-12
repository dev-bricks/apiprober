"""
ApiProber.core.config -- Konfigurationsmanagement
===================================================
Laedt, validiert und speichert Probe-Konfigurationen.
Pattern: llmauto/core/config.py (DEFAULT + load/save + deepcopy)
"""
import json
import os
from pathlib import Path
from copy import deepcopy

BASE_DIR = Path(__file__).resolve().parent.parent

# Placeholder stored instead of real credentials when a config is persisted
REDACTED_PLACEHOLDER = "***REDACTED***"

# Gitignored overlay file for local values, especially credentials
LOCAL_CONFIG_NAME = "config.local.json"

# Environment variables take precedence over both config files
ENV_AUTH_VALUE = "APIPROBER_AUTH_VALUE"
ENV_AUTH_TYPE = "APIPROBER_AUTH_TYPE"

# Keys that must never be written to the tracked config.json
SECRET_KEYS = {"auth.value"}

DEFAULT_CONFIG = {
    "delay_ms": 500,
    "max_requests": 500,
    "max_depth": 3,
    "timeout_seconds": 30,
    "connect_timeout_s": 10,
    "read_timeout_s": 30,
    "max_retries": 2,
    "user_agent": "ApiProber/0.1 (github.com/dev-bricks/apiprober; passive-discovery)",
    "respect_robots_txt": True,
    "skip_destructive": True,
    "strategies": ["openapi", "wordlist", "pattern", "response_driven"],
    "auth": {
        "type": "none",
        "value": ""
    },
    "wordlists": [
        "common_rest.txt",
        "swagger_paths.txt",
        "auth_endpoints.txt",
        "admin_paths.txt"
    ],
    "pattern_versions": [1, 2, 3],
    "pattern_resources": [
        "users", "posts", "comments", "items", "products",
        "orders", "categories", "tags", "articles", "pages",
        "search", "settings", "config", "health", "status",
        "albums", "photos", "videos", "contacts", "customers",
        "tickets", "reviews", "collections", "templates"
    ],
    "methods_safe": ["GET", "HEAD", "OPTIONS"],
    "methods_all": ["GET", "HEAD", "OPTIONS", "POST", "PUT", "PATCH", "DELETE"],
    "export_dir": "exports",
    "db_path": "data/api_prober.db"
}


def load_config(config_path=None):
    """Laedt Konfiguration aus JSON-Datei, merged mit Defaults.

    Reihenfolge (spaetere Quellen ueberschreiben fruehere):
    1. DEFAULT_CONFIG
    2. config.json (getrackt, KEINE Secrets)
    3. config.local.json (gitignored Overlay, z.B. auth.value)
    4. Umgebungsvariablen APIPROBER_AUTH_VALUE / APIPROBER_AUTH_TYPE
    """
    if config_path is None:
        config_path = BASE_DIR / "config.json"
    else:
        config_path = Path(config_path)
    local_path = config_path.parent / LOCAL_CONFIG_NAME

    config = deepcopy(DEFAULT_CONFIG)
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            user_config = json.load(f)
        _deep_merge(config, user_config)
    if local_path.exists():
        with open(local_path, "r", encoding="utf-8") as f:
            local_config = json.load(f)
        _deep_merge(config, local_config)

    # Environment overrides (highest precedence, never touch any file)
    env_auth_type = os.environ.get(ENV_AUTH_TYPE)
    if env_auth_type:
        config.setdefault("auth", {})["type"] = env_auth_type
    env_auth_value = os.environ.get(ENV_AUTH_VALUE)
    if env_auth_value:
        config.setdefault("auth", {})["value"] = env_auth_value

    return config


def save_config(config, config_path=None):
    """Speichert Konfiguration als JSON."""
    if config_path is None:
        config_path = BASE_DIR / "config.json"
    else:
        config_path = Path(config_path)

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


def set_config_value(key, value, config_path=None):
    """Setzt einen Konfigurationswert persistent (Punkt-Notation moeglich).

    Secrets (SECRET_KEYS, z.B. auth.value) landen in der gitignorten
    config.local.json, alle anderen Werte in config.json. Es wird nur die
    jeweilige Roh-Datei geschrieben -- Defaults werden NICHT zurueckgeschrieben
    (kein Config-Drift in der getrackten Datei).

    Returns:
        Path: Datei, in die geschrieben wurde.
    """
    if config_path is None:
        config_path = BASE_DIR / "config.json"
    else:
        config_path = Path(config_path)

    if key in SECRET_KEYS:
        target_path = config_path.parent / LOCAL_CONFIG_NAME
    else:
        target_path = config_path

    raw = {}
    if target_path.exists():
        with open(target_path, "r", encoding="utf-8") as f:
            raw = json.load(f)

    node = raw
    parts = key.split(".")
    for part in parts[:-1]:
        if part not in node or not isinstance(node[part], dict):
            node[part] = {}
        node = node[part]
    node[parts[-1]] = value

    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(raw, f, indent=4, ensure_ascii=False)
        f.write("\n")
    return target_path


def get_db_path(config=None):
    """Gibt absoluten Pfad zur DB zurueck."""
    if config is None:
        config = load_config()
    db_rel = config.get("db_path", DEFAULT_CONFIG["db_path"])
    return BASE_DIR / db_rel


def get_export_dir(config=None):
    """Gibt absoluten Pfad zum Export-Verzeichnis zurueck."""
    if config is None:
        config = load_config()
    export_rel = config.get("export_dir", DEFAULT_CONFIG["export_dir"])
    return BASE_DIR / export_rel


def redact_config(config):
    """Gibt eine Kopie der Config ohne Klartext-Credentials zurueck.

    auth.value wird durch REDACTED_PLACEHOLDER ersetzt, damit Tokens und
    Passwoerter niemals in der SQLite-DB (probe_runs.config_json) landen.
    """
    redacted = deepcopy(config)
    auth = redacted.get("auth")
    if isinstance(auth, dict) and auth.get("value"):
        auth["value"] = REDACTED_PLACEHOLDER
    return redacted


def _deep_merge(base, override):
    """Rekursiver Merge: override ueberschreibt base in-place."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
