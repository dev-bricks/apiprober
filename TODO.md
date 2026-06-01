# Pre-Release TODO: ApiProber

**Audit Date:** 2026-05-27
**Auditor:** GPT / Codex automation
**Target Repo:** `dev-bricks/apiprober`

---

## BLOCKER

- [x] **Secrets:** No secret patterns found in tracked text files.
- [x] **Private Data:** No known private email patterns found outside allowed metadata.
- [x] **Hardcoded Paths:** No personal Windows or Unix home paths found.
- [x] **Database Files:** No `.db` files are tracked.
- [x] **.env Files:** No `.env` files are tracked.
- [x] **BACH Internals:** No BACH-internal documents are tracked.
- [x] **.gitignore:** Minimum gate entries are present.
- [x] **LICENSE:** MIT license file is present.
- [x] **README.md:** English README is present; German liability section is intentional and uses real umlauts.

---

## HIGH PRIORITY

- [x] Add `CHANGELOG.md` before the next tagged release.
- [ ] Decide whether generated local probe outputs should stay entirely in `data/` and `exports/` or move to a configurable runtime directory.

---

## MEDIUM PRIORITY

- [x] Add CI for the smoke test.
- [ ] Expand tests around auth handling, robots.txt decisions and export output.
- [ ] Review whether the package import path should be normalized before PyPI publication.

---

## LOW PRIORITY

- [ ] Add badges after CI exists.
- [ ] Publish to PyPI after a final release review.

---

## STATUS

| Category | Status | Notes |
|----------|--------|-------|
| Secrets | PASS | Gate scan found no secret patterns. |
| Private Data (PII) | PASS | Known private email patterns were not found. |
| .gitignore | PASS | Minimum entries are present. |
| Language (English) | PASS | README passes the gate; German liability section is intentional. |
| BACH Internals | PASS | No BACH-internal files are tracked. |
| Database Files | PASS | No `.db` files are tracked. |
| README.md | PASS | Present and release-oriented. |
| LICENSE | PASS | MIT license present. |
| **Overall** | **READY** | Final Gate Check passes after this audit. |

**Audit Date:** 2026-05-27
**Gate Check Exit Code:** `0`

---

*Template basis: MODULES/_templates/TODO_TEMPLATE.md*
