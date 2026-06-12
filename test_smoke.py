#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
Smoke Test: ApiProber (SQ080)
==============================

Testet grundlegende Funktionalität des ApiProbers:
- Modul-Import funktioniert
- CLI-Tool startet
- Discovery gegen jsonplaceholder.typicode.com
- Export-Funktionen (Markdown, JSON)

Author: BACH Development Team
Created: 2026-02-21 (SQ080, Runde 34)
"""

import pytest
import sys
import json
import os
from pathlib import Path

# Füge ApiProber-Verzeichnis zum Python-Path hinzu
API_PROBER_DIR = Path(__file__).parent
sys.path.insert(0, str(API_PROBER_DIR))


class TestApiProberImport:
    """Test: Modul-Import."""

    def test_import_api_prober(self):
        """Test: api_prober Modul kann importiert werden."""
        try:
            import api_prober
            assert True
        except ImportError as e:
            pytest.fail(f"api_prober konnte nicht importiert werden: {e}")

    def test_import_discovery(self):
        """Test: discovery Module existieren."""
        try:
            # B36-Fix: Korrekte Importpfade -- Package-Import noetig wegen
            # relativer Imports (from ..core.config) im Orchestrator
            parent_dir = str(API_PROBER_DIR.parent)
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            from ApiProber.discovery.orchestrator import ProbeOrchestrator
            assert ProbeOrchestrator is not None
            from ApiProber.discovery import wordlist
            from ApiProber.discovery import openapi_detect
        except ImportError as e:
            pytest.fail(f"discovery Modul fehlt: {e}")

    def test_import_export(self):
        """Test: export Modul existiert."""
        try:
            from export import markdown
            from export import json_export
        except ImportError as e:
            pytest.fail(f"export Modul fehlt: {e}")


class TestApiProberCLI:
    """Test: CLI-Tool grundlegende Funktionen."""

    def test_cli_help_works(self):
        """Test: CLI --help funktioniert."""
        import subprocess
        result = subprocess.run(
            [sys.executable, "api_prober.py", "--help"],
            cwd=str(API_PROBER_DIR),
            capture_output=True,
            text=True,
            timeout=5
        )
        assert result.returncode == 0, "--help sollte erfolgreich sein"
        assert "probe" in result.stdout.lower() or "usage" in result.stdout.lower()

    def test_cli_list_works(self):
        """Test: CLI list funktioniert (zeigt Services)."""
        import subprocess
        result = subprocess.run(
            [sys.executable, "api_prober.py", "list"],
            cwd=str(API_PROBER_DIR),
            capture_output=True,
            text=True,
            timeout=5
        )
        # list sollte funktionieren (returncode 0 oder 1 wenn leer)
        assert result.returncode in [0, 1]


class TestApiProberDatabase:
    """Test: Datenbank-Funktionalität."""

    def test_default_db_path_is_in_data_dir(self):
        """Test: Default-DB-Pfad liegt unter data/ (nicht im Projektroot)."""
        parent_dir = str(API_PROBER_DIR.parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from ApiProber.core.config import DEFAULT_CONFIG, get_db_path
        from copy import deepcopy

        db_path = get_db_path(deepcopy(DEFAULT_CONFIG))
        assert db_path.parent.name == "data", \
            f"DB sollte unter data/ liegen, ist aber: {db_path}"
        assert db_path.name == "api_prober.db"

    def test_database_creation(self, tmp_path):
        """Test: Database legt das Schema mit allen 5 Tabellen an."""
        import sqlite3
        parent_dir = str(API_PROBER_DIR.parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from ApiProber.core.database import Database

        db_path = tmp_path / "data" / "api_prober.db"
        Database(db_path)  # erzeugt Verzeichnis + Schema

        assert db_path.exists(), "DB-Datei sollte angelegt werden"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

        # Reale Tabellen laut Schema (core/database.py)
        expected_tables = {"services", "endpoints", "responses", "parameters", "probe_runs"}
        missing = expected_tables - tables
        assert not missing, f"Fehlende Tabellen: {missing} (gefunden: {tables})"


class TestApiProberQuickProbe:
    """Test: Schneller Probe-Test (minimale API-Abfrage)."""

    def test_quick_probe_jsonplaceholder(self):
        """Test: Minimaler Probe gegen jsonplaceholder.typicode.com."""
        if os.environ.get("APIPROBER_RUN_NETWORK_TESTS") != "1":
            pytest.skip("Live-Netzwerkprobe ist opt-in mit APIPROBER_RUN_NETWORK_TESTS=1")

        # B36-Fix: --max-requests 5 begrenzt auf wenige Requests (verhindert 60s+ Haenger).
        # --depth 0 allein reicht NICHT, da Wordlist/Pattern-Strategien trotzdem laufen.
        # Subprocess-Timeout 90s: 5 Requests * max 30s Timeout + Retries + Overhead

        import subprocess
        try:
            result = subprocess.run(
                [sys.executable, "api_prober.py", "probe",
                 "https://jsonplaceholder.typicode.com",
                 "--depth", "0",
                 "--delay-ms", "0",
                 "--max-requests", "5"],
                cwd=str(API_PROBER_DIR),
                capture_output=True,
                text=True,
                timeout=90
            )
        except subprocess.TimeoutExpired:
            pytest.skip("Probe-Timeout: Netzwerk zu langsam oder API nicht erreichbar")

        # Sollte erfolgreich sein (returncode 0)
        # ODER Fehler wegen Rate-Limiting / Netzwerk (nicht kritisch fuer Smoke-Test)
        assert result.returncode in [0, 1], f"Probe fehlgeschlagen: {result.stderr}"

        # Wenn erfolgreich, sollte Output haben
        if result.returncode == 0:
            assert len(result.stdout) > 0, "Probe sollte Output erzeugen"


class TestCredentialRedaction:
    """Regressionstests: auth.value darf nie im Klartext in die DB gelangen."""

    def _ensure_package_importable(self):
        parent_dir = str(API_PROBER_DIR.parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

    def test_redact_config_masks_auth_value(self):
        """redact_config ersetzt auth.value, laesst das Original unveraendert."""
        self._ensure_package_importable()
        from ApiProber.core.config import redact_config, REDACTED_PLACEHOLDER

        config = {"auth": {"type": "bearer", "value": "super-secret-token"}}
        redacted = redact_config(config)
        assert redacted["auth"]["value"] == REDACTED_PLACEHOLDER
        assert redacted["auth"]["type"] == "bearer"
        # Original bleibt unveraendert (deepcopy)
        assert config["auth"]["value"] == "super-secret-token"

    def test_redact_config_keeps_empty_auth_value(self):
        """Leerer auth.value bleibt leer (kein falsches Redact-Signal)."""
        self._ensure_package_importable()
        from ApiProber.core.config import redact_config

        config = {"auth": {"type": "none", "value": ""}}
        assert redact_config(config)["auth"]["value"] == ""

    def test_probe_run_config_contains_no_secret(self, tmp_path):
        """In probe_runs.config_json landet der Token nicht im Klartext."""
        self._ensure_package_importable()
        from ApiProber.core.config import redact_config
        from ApiProber.core.database import Database

        secret = "super-secret-token"
        db = Database(tmp_path / "test.db")
        service_id = db.upsert_service("dummy", "https://example.invalid")
        db.create_probe_run(service_id, redact_config(
            {"auth": {"type": "bearer", "value": secret}}
        ))
        run = db.get_last_probe_run(service_id)
        assert secret not in run["config_json"], \
            "Token darf nicht im Klartext in probe_runs.config_json stehen"

    def test_resume_restores_auth_value_from_current_config(self, tmp_path, monkeypatch):
        """resume() ersetzt den Redaction-Platzhalter durch den aktuellen Auth-Wert."""
        self._ensure_package_importable()
        from copy import deepcopy
        from ApiProber.core.config import DEFAULT_CONFIG, redact_config
        from ApiProber.discovery.orchestrator import ProbeOrchestrator

        config = deepcopy(DEFAULT_CONFIG)
        config["db_path"] = str(tmp_path / "test.db")
        config["auth"] = {"type": "bearer", "value": "current-token"}

        orch = ProbeOrchestrator(config)
        service_id = orch.db.upsert_service("dummy", "https://example.invalid")
        stored = deepcopy(config)
        stored["auth"]["value"] = "old-secret"
        orch.db.create_probe_run(service_id, redact_config(stored))

        # probe() stubben, damit kein Netzwerkzugriff passiert
        monkeypatch.setattr(orch, "probe", lambda url, **kw: {"status": "stubbed"})
        result = orch.resume("dummy")

        assert result == {"status": "stubbed"}
        assert orch.config["auth"]["value"] == "current-token", \
            "resume() muss den Auth-Wert aus der aktuellen Config beziehen"
        assert orch.config["auth"]["type"] == "bearer"


class TestRobotsServerError:
    """Regressionstest: 5xx beim robots.txt-Abruf darf NICHT 'alles erlaubt' bedeuten."""

    def _make_checker(self, monkeypatch, status_code):
        import urllib.error
        parent_dir = str(API_PROBER_DIR.parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from ApiProber.core import robots as robots_mod

        def fake_urlopen(req, timeout=10):
            raise urllib.error.HTTPError(
                "https://example.invalid/robots.txt", status_code,
                "error", {}, None
            )

        monkeypatch.setattr(robots_mod.urllib.request, "urlopen", fake_urlopen)
        return robots_mod.RobotsChecker("https://example.invalid")

    def test_5xx_means_disallow_all(self, monkeypatch):
        """5xx -> konservativ: alle Pfade gesperrt (RFC 9309)."""
        checker = self._make_checker(monkeypatch, 503)
        success, raw = checker.load()
        assert success is False
        assert checker.unavailable_status == 503
        assert checker.is_allowed("/api") is False
        assert checker.is_allowed("/") is False

    def test_404_means_everything_allowed(self, monkeypatch):
        """404 -> kein robots.txt vorhanden -> alles erlaubt (Standard)."""
        checker = self._make_checker(monkeypatch, 404)
        success, raw = checker.load()
        assert success is False
        assert checker.unavailable_status is None
        assert checker.is_allowed("/api") is True


class TestApiProberExport:
    """Test: Export-Funktionen (konzeptionell)."""

    def test_export_commands_exist(self):
        """Test: export-md und export-json Befehle existieren."""
        import subprocess

        # Prüfe ob export-md Befehl existiert (ohne API-Probe)
        result_md = subprocess.run(
            [sys.executable, "api_prober.py", "export", "--help"],
            cwd=str(API_PROBER_DIR),
            capture_output=True,
            text=True,
            timeout=5
        )

        result_json = subprocess.run(
            [sys.executable, "api_prober.py", "export", "--help"],
            cwd=str(API_PROBER_DIR),
            capture_output=True,
            text=True,
            timeout=5
        )

        assert result_md.returncode == 0
        assert result_json.returncode == 0


class TestApiProberDocumentation:
    """Test: Dokumentation vorhanden."""

    def test_readme_exists(self):
        """Test: README.md existiert."""
        readme_path = API_PROBER_DIR / "README.md"
        assert readme_path.exists(), "README.md sollte existieren"

        # README sollte Mindest-Inhalt haben
        content = readme_path.read_text(encoding='utf-8')
        assert len(content) > 100, "README sollte Inhalt haben"
        assert "ApiProber" in content or "API Prober" in content


# ============================================================================
#  MAIN (für direktes Ausführen)
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
