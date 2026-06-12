<p align="center">
  <img src="ApiProber_logo.jpg" alt="ApiProber" width="700">
</p>

# ApiProber -- Passive API Discovery and Documentation Tool

[![ApiProber smoke tests](https://github.com/dev-bricks/apiprober/actions/workflows/tests.yml/badge.svg)](https://github.com/dev-bricks/apiprober/actions/workflows/tests.yml)

ApiProber is a zero-dependency Python CLI for passive API discovery. It helps
developers and maintainers map undocumented REST services, compare live
behavior with API documentation, persist observations in SQLite, and export
Markdown or JSON documentation.

**Author:** Lukas Geiger | **License:** MIT | **Python:** 3.8+ (stdlib only)

---

## Start Here

| Goal | Command or File |
|---|---|
| Try the CLI | `python api_prober.py --help` |
| Map an authorized API | `python api_prober.py probe <base-url>` |
| Export documentation | `python api_prober.py export <service> --format md` |
| Read machine context | [`llms.txt`](llms.txt) |
| Report a vulnerability privately | [`SECURITY.md`](SECURITY.md) |

---

## Best Fit

- Internal REST services where no OpenAPI file exists
- Legacy APIs that need lightweight endpoint documentation
- Documentation audits where live behavior should be compared with expected routes
- Local-first reconnaissance before writing a proper client or SDK
- Passive security review with explicit authorization

ApiProber is not an exploit framework, vulnerability scanner, load tester, or
fuzzer. Use it only on APIs you own or are allowed to assess.

---

## Features

- **Multi-Strategy Discovery:** OpenAPI detection, wordlist probing, pattern expansion, HATEOAS link following
- **Rate Limiting:** Configurable delay between requests (default: 500ms)
- **robots.txt Compliance:** Automatic respect for access restrictions
- **Auth Support:** Bearer token, API key, Basic auth
- **JSON Schema Extraction:** Automatic schema inference from response bodies
- **SQLite Persistence:** All results stored in a local database
- **Export:** Markdown and JSON (OpenAPI-like)
- **Resume:** Continue interrupted probing sessions
- **Ethical by Default:** Only passive exploration, no fuzzing or destructive methods
- **Zero Dependencies:** Pure Python stdlib (urllib, json, sqlite3, argparse, pathlib)

---

## Installation

No installation required -- works with Python 3.8+ standard library only.

```bash
git clone https://github.com/dev-bricks/apiprober.git
cd apiprober

# Run directly from the repository root
python api_prober.py --help

# Or install as package
pip install -e .
apiprober --help
```

---

## Quick Start

### Probe an API

```bash
# Basic probe
python api_prober.py probe https://jsonplaceholder.typicode.com

# Deep probe with custom delay
python api_prober.py probe https://api.example.com --depth 2 --delay-ms 1000

# Authenticated probe
python api_prober.py probe https://api.example.com --auth-type bearer --auth-value "YOUR_TOKEN"
```

### Manage Services

```bash
# List all probed services
python api_prober.py list

# Show details for a specific service
python api_prober.py status jsonplaceholder

# Resume interrupted probing
python api_prober.py resume jsonplaceholder
```

### Export Results

```bash
# Export as Markdown documentation
python api_prober.py export jsonplaceholder --format md

# Export as JSON (OpenAPI-like)
python api_prober.py export jsonplaceholder --format json
```

### Configuration

```bash
# Show current config
python api_prober.py config --show

# Set values
python api_prober.py config --set delay_ms 1000
python api_prober.py config --set auth.type bearer
```

### Credential Handling

Credentials are kept out of the tracked `config.json` and out of the local
SQLite database:

- **Recommended:** set the environment variables `APIPROBER_AUTH_VALUE` (and
  optionally `APIPROBER_AUTH_TYPE`). They take precedence over all config
  files and are never written to disk.
- `python api_prober.py config --set auth.value "TOKEN"` writes the value to
  `config.local.json` -- a gitignored overlay file next to `config.json` --
  never to the tracked `config.json`.
- Config resolution order: defaults -> `config.json` -> `config.local.json`
  -> environment variables.
- Probe run configurations stored in the SQLite database have `auth.value`
  redacted (`***REDACTED***`); `resume` re-reads the credential from the
  current config or environment.

---

## Discovery Strategies

ApiProber uses four strategies in priority order:

1. **OpenAPI Detection** (Priority 1): Checks for `/swagger.json`, `/openapi.json`, `/api-docs`, etc.
2. **Wordlist Probing** (Priority 2): Tests ~140 common REST endpoint paths
3. **Pattern Expansion** (Priority 3): Expands `/api/v{1,2,3}/{resource}` patterns
4. **Response-Driven / HATEOAS** (Priority 4): Follows links discovered in response bodies

---

## Security and Ethics

ApiProber is designed for responsible API exploration:

- **Default: Read-only** -- Only GET, HEAD, OPTIONS (no POST/PUT/DELETE unless `--test-all-methods` flag)
- **Built-in rate limiting** -- Configurable delay between requests
- **robots.txt compliance** -- Automatically respects access restrictions
- **Transparent User-Agent** -- `ApiProber/0.1 (github.com/dev-bricks/apiprober; passive-discovery)`
- **No fuzzing, no exploitation** -- Purely passive discovery

---

## Project Structure

```
ApiProber/
+-- api_prober.py        CLI entry point
+-- config.json          Default configuration (no secrets)
+-- config.local.json    Local overrides incl. auth.value -- gitignored
+-- core/                Core modules
|   +-- config.py        Configuration management
|   +-- database.py      SQLite persistence layer
|   +-- http_client.py   HTTP client with rate limiting
|   +-- robots.py        robots.txt parser
|   +-- schema_extractor.py  JSON schema inference
+-- discovery/           Discovery strategies
|   +-- orchestrator.py  Strategy coordination
|   +-- openapi_detect.py  OpenAPI/Swagger detection
|   +-- wordlist.py      Wordlist-based probing
|   +-- pattern.py       Pattern expansion
|   +-- response_driven.py  HATEOAS link following
|   +-- method_tester.py  HTTP method testing
+-- export/              Export formats
|   +-- json_export.py   JSON export
|   +-- markdown.py      Markdown documentation generator
+-- wordlists/           Probe wordlists (~140 paths)
|   +-- common_rest.txt  Common REST endpoints
|   +-- admin_paths.txt  Admin/management paths
|   +-- auth_endpoints.txt  Authentication endpoints
|   +-- swagger_paths.txt  Swagger/OpenAPI paths
+-- data/                Runtime data (api_prober.db) -- gitignored
+-- exports/             Generated documentation -- gitignored
```

---

## Use Cases

- **Documenting** undocumented internal APIs
- **Validating** API documentation against actual behavior
- **Finding** reachable endpoints in systems you are authorized to assess
- **Generating** API documentation for legacy systems
- **Security auditing** through passive reconnaissance only

---

## Discoverability Keywords

`passive API discovery`, `REST API documentation generator`, `OpenAPI detection`,
`HATEOAS link crawler`, `local-first API reconnaissance`, `zero-dependency Python
CLI`, `SQLite API inventory`, `ethical API probing`, `authorized API inventory`,
`REST endpoint mapper`

ApiProber is unrelated to Cloudprober, probe-rs, code-search probe tools, and
active uptime monitoring systems. Its focus is local, rate-limited REST API
surface documentation for systems you own or are explicitly allowed to assess.

---

## License

MIT License. See [LICENSE](LICENSE).

---

## Development

Run the local smoke tests without live network probing:

```bash
python -m pytest -q
python -m compileall -q .
```

The live `jsonplaceholder.typicode.com` probe is opt-in for manual checks:

```bash
set APIPROBER_RUN_NETWORK_TESTS=1
python -m pytest -q test_smoke.py
```

---

## Author

Lukas Geiger -- [github.com/lukisch](https://github.com/lukisch)

Repository -- [dev-bricks/apiprober](https://github.com/dev-bricks/apiprober)

---

## Haftung / Liability

Dieses Projekt ist eine **unentgeltliche Open-Source-Schenkung** im Sinne der §§ 516 ff. BGB. Die Haftung des Urhebers ist gemäß **§ 521 BGB** auf **Vorsatz und grobe Fahrlässigkeit** beschränkt. Ergänzend gelten die Haftungsausschlüsse aus der MIT-Lizenz.

Nutzung auf eigenes Risiko. Keine Wartungszusage, keine Verfügbarkeitsgarantie, keine Gewähr für Fehlerfreiheit oder Eignung für einen bestimmten Zweck.

This project is an unpaid open-source donation. Liability is limited to intent and gross negligence (§ 521 German Civil Code). Use at your own risk. No warranty, no maintenance guarantee, no fitness-for-purpose assumed.
