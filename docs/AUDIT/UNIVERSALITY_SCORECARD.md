# Universality Scorecard

**Date:** 2026-01-29
**Auditor:** Gemini

## Overall System Score: 5.8 / 10
**Verdict:** The "Logical Core" is universal, but the "Physical Shell" (Infrastructure/Tests) is brittle.

---

## Layer Assessment

### 1. Configuration Layer
**Score:** 6 / 10
**Status:** ⚠️ Inconsistent
-   ✅ **Dynamic Loading:** `LanguageManager` correctly loads `*.yaml` files.
-   ✅ **JIT Generation:** `fetch_lang_config.py` enables zero-day setup for new languages.
-   ❌ **Schema Chaos:** `de.yaml`, `pl.yaml`, and `en.yaml` have different keys. This risks runtime crashes (`KeyError`).
-   ❌ **Hardcoded Refs:** `en.yaml` has hardcoded empty map.

### 2. Extraction Pipeline (Core)
**Score:** 9 / 10
**Status:** ✅ Robust
-   ✅ **Config Driven:** `extract_infoboxes.py` reads everything from config.
-   ✅ **Dynamic Paths:** No hardcoded filenames in the logic.
-   ❌ **Minor:** `enrich_neo4j_titles.py` tool has a hardcoded path hack.

### 3. Database Layer
**Score:** 10 / 10
**Status:** 🏆 Exemplary
-   ✅ **Generic Schema:** SQLite tables are identical for all languages.
-   ✅ **Federated Design:** File-per-language (`de.db`, `pl.db`) scales infinitely without collision.

### 4. API Layer
**Score:** 10 / 10
**Status:** 🏆 Exemplary
-   ✅ **Dynamic Routing:** Endpoints validate `{lang}` against loaded settings.
-   ✅ **Dynamic Drivers:** Neo4j connection pool initializes based on settings.

### 5. Infrastructure Layer
**Score:** 2 / 10
**Status:** ❌ Critical Failure
-   ❌ **Hardcoded Scripts:** `dev.sh` manually lists `pl` and `de` commands.
-   ❌ **Manual Ports:** Ports are hardcoded in the script, ignoring `infrastructure.yaml`.
-   ❌ **Impact:** Adding `es` requires rewriting shell scripts.

### 6. Testing Layer
**Score:** 1 / 10
**Status:** ❌ Total Failure
-   ❌ **Hardcoded Iteration:** Tests loop `["de", "pl"]` manually.
-   ❌ **Hardcoded Data:** QIDs (e.g., Berlin Q64) are hardcoded in Python files.
-   ❌ **Impact:** Tests verify "The DE/PL System", not "The Universal System".

---

## Pass/Fail Criteria for "Adding Spanish"

| Criteria | Status | Note |
| :--- | :--- | :--- |
| **Ingest Data** | **PASS** | Core pipeline can process `es`. |
| **Spin up DB** | **FAIL** | `dev.sh` won't start `neo4j-es`. |
| **Verify Data** | **FAIL** | Tests won't run for `es`. |
| **Serve API** | **PASS** | If DB is manually started, API will serve it. |
