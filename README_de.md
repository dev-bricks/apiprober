<p align="center">
  <img src="assets/banner_v2.svg" alt="ApiProber" width="100%" />
</p>

<p align="right">
  <b>🇩🇪 Deutsch</b> | <a href="README.md">🇬🇧 English</a>
</p>

# ApiProber -- Passives API-Discovery- und Dokumentations-Tool

[![ApiProber smoke tests](https://github.com/dev-bricks/apiprober/actions/workflows/tests.yml/badge.svg)](https://github.com/dev-bricks/apiprober/actions/workflows/tests.yml)

ApiProber ist ein abhängigkeitsfreies Python-CLI für passives API-Discovery. Es hilft Entwicklern und Maintainern, undokumentierte REST-Dienste zu kartografieren, das Live-Verhalten mit der API-Dokumentation zu vergleichen, Beobachtungen in SQLite zu persistieren und Markdown- oder JSON-Dokumentationen zu exportieren.

**Autor:** Lukas Geiger | **Lizenz:** MIT | **Python:** 3.8+ (nur Standardbibliothek)

---

## Einstieg

| Ziel | Befehl oder Datei |
|---|---|
| CLI ausprobieren | `python api_prober.py --help` |
| Autorisierte API kartografieren | `python api_prober.py probe <base-url>` |
| Dokumentation exportieren | `python api_prober.py export <service> --format md` |
| Maschinenlesbaren Kontext lesen | [`llms.txt`](llms.txt) |
| Schwachstelle vertraulich melden | [`SECURITY.md`](SECURITY.md) |

---

## Einsatzbereiche

- Interne REST-Dienste, für die keine OpenAPI-Datei existiert
- Legacy-APIs, die eine leichtgewichtige Endpunkt-Dokumentation benötigen
- Dokumentations-Audits, bei denen das Live-Verhalten mit den erwarteten Routen verglichen werden soll
- Local-First-Sondierung vor dem Schreiben eines eigenen Clients oder SDKs
- Passive Sicherheitsüberprüfungen mit expliziter Autorisierung

ApiProber ist kein Exploit-Framework, Schwachstellen-Scanner, Fuzzer oder Lasttester. Nutzen Sie es nur für APIs, die Sie besitzen oder zu deren Überprüfung Sie ausdrücklich berechtigt sind.

---

## Funktionen

- **Multi-Strategie-Erkennung:** OpenAPI-Erkennung, Wordlist-Probing, Pattern-Expansion (Mustererweiterung), Verfolgung von HATEOAS-Links
- **Rate Limiting:** Konfigurierbare Verzögerung zwischen Anfragen (Standard: 500 ms)
- **robots.txt-Konformität:** Automatische Berücksichtigung von Zugriffsbeschränkungen
- **Authentifizierungs-Unterstützung:** Bearer-Token, API-Key, Basic-Auth
- **JSON-Schema-Extraktion:** Automatische Ableitung von Schemata aus Antwort-Bodies
- **SQLite-Persistenz:** Alle Ergebnisse werden in einer lokalen Datenbank gespeichert
- **Export:** Markdown und JSON (OpenAPI-ähnlich)
- **Fortsetzen:** Fortführung unterbrochener Probing-Sitzungen
- **Standardmäßig ethisch:** Nur passive Erkundung, kein Fuzzing oder destruktive Methoden
- **Keine Abhängigkeiten (Zero-Dependency):** Reines Python aus der Standardbibliothek (urllib, json, sqlite3, argparse, pathlib)

---

## Installation

Keine Installation erforderlich -- funktioniert ausschließlich mit der Python 3.8+ Standardbibliothek.

```bash
git clone https://github.com/dev-bricks/apiprober.git
cd apiprober

# Direkt aus dem Repository-Root ausführen
python api_prober.py --help

# Oder als Paket installieren
pip install -e .
apiprober --help
```

---

## Schnellstart

### Eine API untersuchen

```bash
# Einfache Untersuchung
python api_prober.py probe https://jsonplaceholder.typicode.com

# Tiefe Untersuchung mit benutzerdefinierter Verzögerung
python api_prober.py probe https://api.example.com --depth 2 --delay-ms 1000

# Authentifizierte Untersuchung
python api_prober.py probe https://api.example.com --auth-type bearer --auth-value "IHR_TOKEN"
```

### Dienste verwalten

```bash
# Alle untersuchten Dienste auflisten
python api_prober.py list

# Details für einen bestimmten Dienst anzeigen
python api_prober.py status jsonplaceholder

# Unterbrochene Untersuchung fortsetzen
python api_prober.py resume jsonplaceholder
```

### Ergebnisse exportieren

```bash
# Als Markdown-Dokumentation exportieren
python api_prober.py export jsonplaceholder --format md

# Als JSON (OpenAPI-ähnlich) exportieren
python api_prober.py export jsonplaceholder --format json
```

### Konfiguration

```bash
# Aktuelle Konfiguration anzeigen
python api_prober.py config --show

# Werte festlegen
python api_prober.py config --set delay_ms 1000
python api_prober.py config --set auth.type bearer
```

### Umgang mit Anmeldedaten

Anmeldedaten (Credentials) werden außerhalb der versionierten `config.json` und der lokalen SQLite-Datenbank gehalten:

- **Empfohlen:** Setzen Sie die Umgebungsvariablen `APIPROBER_AUTH_VALUE` (und optional `APIPROBER_AUTH_TYPE`). Diese haben Vorrang vor allen Konfigurationsdateien und werden niemals auf die Festplatte geschrieben.
- `python api_prober.py config --set auth.value "TOKEN"` schreibt den Wert in `config.local.json` -- eine gitignorierte Overlay-Datei neben `config.json` -- niemals in die versionierte `config.json`.
- Konfigurationsauflösung: Standardwerte -> `config.json` -> `config.local.json` -> Umgebungsvariablen.
- In der SQLite-Datenbank gespeicherte Run-Konfigurationen haben `auth.value` zensiert (`***REDACTED***`); `resume` liest das Credential erneut aus der aktuellen Konfiguration oder Umgebung ein.

---

## Erkennungsstrategien

ApiProber verwendet vier Strategien in absteigender Priorität:

1. **OpenAPI-Erkennung** (Priorität 1): Prüft auf `/swagger.json`, `/openapi.json`, `/api-docs` etc.
2. **Wordlist-Probing** (Priorität 2): Testet ~140 gängige REST-Endpunkt-Pfade.
3. **Pattern-Expansion** (Priorität 3): Erweitert Muster wie `/api/v{1,2,3}/{resource}`.
4. **Response-Driven / HATEOAS** (Priorität 4): Folgt in Antwort-Bodies entdeckten Links.

---

## Sicherheit und Ethik

ApiProber ist für die verantwortungsvolle API-Erkundung konzipiert:

- **Standardmäßig schreibgeschützt (Read-only):** Nur GET, HEAD, OPTIONS (keine POST/PUT/DELETE-Anfragen ohne das Flag --test-all-methods).
- **Integriertes Rate Limiting:** Konfigurierbare Verzögerung zwischen Anfragen.
- **robots.txt-Konformität:** Berücksichtigt automatisch Zugriffsbeschränkungen.
- **Transparenter User-Agent:** `ApiProber/0.1 (github.com/dev-bricks/apiprober; passive-discovery)`
- **Kein Fuzzing, kein Exploiting:** Ausschließlich passive Erkennung.

---

## Projektstruktur

```
ApiProber/
+-- api_prober.py        CLI-Einstiegspunkt
+-- config.json          Standardkonfiguration (keine Geheimnisse)
+-- config.local.json    Lokale Overrides inkl. auth.value -- gitignoriert
+-- core/                Kernmodule
|   +-- config.py        Konfigurationsverwaltung
|   +-- database.py      SQLite-Persistenzschicht
|   +-- http_client.py   HTTP-Client mit Rate Limiting
|   +-- robots.py        robots.txt-Parser
|   +-- schema_extractor.py  JSON-Schema-Inferenz
+-- discovery/           Erkennungsstrategien
|   +-- orchestrator.py  Strategie-Koordination
|   +-- openapi_detect.py  OpenAPI/Swagger-Erkennung
|   +-- wordlist.py      Wordlist-basiertes Probing
|   +-- pattern.py       Pattern-Expansion
|   +-- response_driven.py  HATEOAS-Link-Verfolgung
|   +-- method_tester.py  HTTP-Methoden-Tests
+-- export/              Export-Formate
|   +-- json_export.py   JSON-Export
|   +-- markdown.py      Markdown-Dokumentationsgenerator
+-- wordlists/           Probe-Wordlists (~140 Pfade)
|   +-- common_rest.txt  Gängige REST-Endpunkte
|   +-- admin_paths.txt  Admin- und Managementpfade
|   +-- auth_endpoints.txt  Authentifizierungsendpunkte
|   +-- swagger_paths.txt  Swagger/OpenAPI-Pfade
+-- data/                Laufzeitdaten (api_prober.db) -- gitignoriert
+-- exports/             Generierte Dokumentation -- gitignoriert
```

---

## Anwendungsfälle

- **Dokumentieren** von undokumentierten internen APIs
- **Validieren** der API-Dokumentation gegen tatsächliches Verhalten
- **Finden** erreichbarer Endpunkte in Systemen, zu deren Überprüfung Sie berechtigt sind
- **Generieren** von API-Dokumentation für Legacy-Systeme
- **Sicherheits-Audits** ausschließlich durch passive Aufklärung (Reconnaissance)

---

## Sichtbarkeit & Keywords

`passive API discovery`, `REST API documentation generator`, `OpenAPI detection`, `HATEOAS link crawler`, `local-first API reconnaissance`, `zero-dependency Python CLI`, `SQLite API inventory`, `ethical API probing`, `authorized API inventory`, `REST endpoint mapper`

ApiProber steht in keiner Verbindung zu Cloudprober, probe-rs, aktiven Uptime-Monitoren oder semantischen Code-Suchmaschinen. Der Fokus liegt auf der lokalen, ratenlimitierten Dokumentation autorisierter REST-API-Oberflächen für Systeme, die Sie besitzen oder explizit überprüfen dürfen.

---

## Lizenz

MIT-Lizenz. Siehe [LICENSE](LICENSE).

---

## Entwicklung

Lokale Smoke-Tests ohne live Netzwerkzugriffe ausführen:

```bash
python -m pytest -q
python -m compileall -q .
```

Die Live-Untersuchung von `jsonplaceholder.typicode.com` kann für manuelle Prüfungen zugeschaltet werden:

```bash
set APIPROBER_RUN_NETWORK_TESTS=1
python -m pytest -q test_smoke.py
```

---

## Autor

Lukas Geiger -- [github.com/lukisch](https://github.com/lukisch)

Repository -- [dev-bricks/apiprober](https://github.com/dev-bricks/apiprober)

---

## Haftung / Liability

Dieses Projekt ist eine **unentgeltliche Open-Source-Schenkung** im Sinne der §§ 516 ff. BGB. Die Haftung des Urhebers ist gemäß **§ 521 BGB** auf **Vorsatz und grobe Fahrlässigkeit** beschränkt. Ergänzend gelten die Haftungsausschlüsse aus der MIT-Lizenz.

Nutzung auf eigenes Risiko. Keine Wartungszusage, keine Verfügbarkeitsgarantie, keine Gewähr für Fehlerfreiheit oder Eignung für einen bestimmten Zweck.

This project is an unpaid open-source donation. Liability is limited to intent and gross negligence (§ 521 German Civil Code). Use at your own risk. No warranty, no maintenance guarantee, no fitness-for-purpose assumed.
