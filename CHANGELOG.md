# Changelog

## 2026-07-04

- Security/ethics: robots.txt is now honored for endpoints that came from an
  OpenAPI/Swagger spec, too. Previously such endpoints were probed in the
  method-testing and schema-extraction phases (including POST/PUT/DELETE with
  `--test-all-methods`) without any robots.txt check.
- Rate limiting: the response-driven (HATEOAS) discovery phase now respects the
  `max_requests` budget. Previously it followed unbounded links per round and
  could exceed the configured request limit.
- Added regression tests for both (`test_smoke.py`): request-budget cap in
  response-driven discovery and robots.txt enforcement across discovery sources.

## 2026-06-12

- Updated the smoke-test workflow to `actions/checkout@v6` and `actions/setup-python@v6`.
- Added Python 3.13 to the CI matrix to match the supported classifier in `pyproject.toml`.

## 2026-06-06

- Added a README start table and smoke-test badge for clearer GitHub entry.
- Expanded `llms.txt` with search phrases and disambiguation context.
- Corrected private vulnerability reporting links after the move to `dev-bricks/apiprober`.

## 2026-06-01

- Fixed repository metadata after the move to `dev-bricks/apiprober`.
- Made the flat `ApiProber` package installable through `pyproject.toml`.
- Added a GitHub Actions smoke-test workflow.
- Changed the live network smoke test to opt-in so CI remains deterministic.
- Added `llms.txt` for machine-readable repository context.
- Updated community workflow action versions and input names.
