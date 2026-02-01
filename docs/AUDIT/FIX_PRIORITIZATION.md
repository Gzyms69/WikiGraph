# Fix Prioritization Plan

## Phase 1: Crisis Fixes (Must Fix NOW)
**Goal:** Prevent system breakage and enable safe expansion.

| ID | Component | Issue | Remediation | Effort |
| :--- | :--- | :--- | :--- | :--- |
| **P1-01** | `dev.sh` | Hardcoded language list & ports. | Rewrite `dev.sh` to read `config/infrastructure.yaml` (or use a Python wrapper). | 2h |
| **P1-02** | Configs | Inconsistent YAML Schemas. | Align `de.yaml`, `pl.yaml`, `en.yaml` keys (add missing `text_cleanup`, `suffixes`). | 30m |
| **P1-03** | `LanguageManager` | Accessing non-existent keys. | Add `.get()` safety wrappers or fix schemas (P1-02). | 15m |

## Phase 2: Verification Readiness (Before Adding 'ES')
**Goal:** Enable testing of new languages without code changes.

| ID | Component | Issue | Remediation | Effort |
| :--- | :--- | :--- | :--- | :--- |
| **P2-01** | Tests | Hardcoded `["de", "pl"]` loops. | Refactor tests to import `settings` and loop dynamic languages. | 4h |
| **P2-02** | Test Data | Hardcoded QIDs in scripts. | Move QIDs to `tests/fixtures/{lang}.json`. | 2h |
| **P2-03** | `enrich_neo4j_titles` | Hardcoded path ternary. | Replace with dynamic path construction. | 15m |

## Phase 3: Technical Debt (Post-Launch)
**Goal:** Long-term maintainability.

| ID | Component | Issue | Remediation | Effort |
| :--- | :--- | :--- | :--- | :--- |
| **P3-01** | `extract_infoboxes` | Simple `param_map`. | Enhance parameter mapping for complex languages. | 1d |
| **P3-02** | `verify_neo4j` | Hardcoded node counts. | Move expected counts to config file. | 2h |
