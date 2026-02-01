# Migration Impact Report & Refactoring Plan (COMPLETED)

**Status:** ✅ EXECUTED on 2026-02-01
**Backup:** `backup_1769959076/pre_migration.tar.gz`

## 1. Overview
This document mapped the dependencies affected by the "Clean Slate" reorganization.
Target structure (ACHIEVED):
- `core/tools/` -> `core/pipeline/`
- `core/ingest.py` -> `core/pipeline/ingest.py`
- `core/sqlite_loader.py` -> `core/loaders/sqlite_loader.py`
- `core/parser.py` -> `core/loaders/parser.py`

## 2. Python Import Refactoring (Must be updated)

### A. Imports of `config.language_manager` (8 Files)
These files import `LanguageManager` and must be checked to ensure they can still find it (Config is NOT moving, so these are safe, but listed for completeness).
1. `app/config.py`
2. `app/models.py`
3. `tools/verify_optimization_accuracy.py`
4. `tests/validate_all_accessors.py`
5. `tests/repro_crash.py`
6. `core/tools/extract_infoboxes.py` (Moving to `core/pipeline`)
7. `core/tools/test_infobox_extraction.py` (Moving to `core/pipeline`)
8. `core/parser.py` (Moving to `core/loaders`)

**Action:** Since `config` is remaining in root, relative imports like `from config.language_manager` should work *unless* the moved files use relative `..` imports.
- `core/parser.py` uses `from config.language_manager`. Moving it to `core/loaders/parser.py` makes it deeper. It should still work if run as module, but we must verify `sys.path`.

### B. Imports of `core.tools.*` (1 File)
1. `tests/verify_csv_generation_logic.py`: `from core.tools.prepare_neo4j_csv import load_mappings`
   - **Action:** Replace with `from core.pipeline.prepare_neo4j_csv import load_mappings`

## 3. Subprocess/Script Path Refactoring
The following files call scripts via string paths (subprocess/os.system) and must be updated:

| File | Old Path String | New Path String |
|------|-----------------|-----------------|
| `core/ingest.py` | `core/tools/fetch_sql_dumps.py` | `core/pipeline/fetch_sql_dumps.py` |
| `core/ingest.py` | `core/tools/extract_infoboxes.py` | `core/pipeline/extract_infoboxes.py` |
| `core/ingest.py` | `core/tools/prepare_neo4j_csv.py` | `core/pipeline/prepare_neo4j_csv.py` |
| `core/ingest.py` | `core/tools/run_neo4j_import.sh` | `core/pipeline/run_neo4j_import.sh` |
| `core/ingest.py` | `core/sqlite_loader.py` | `core/loaders/sqlite_loader.py` |
| `tools/profile_extraction.py` | `core/tools/extract_infoboxes.py` | `core/pipeline/extract_infoboxes.py` |
| `tools/analyze_import_pipeline.py` | `core/tools/` | `core/pipeline/` |
| `tools/audit_data_integrity.py` | `core/tools/prepare_neo4j_csv.py` | `core/pipeline/prepare_neo4j_csv.py` |
| `tools/audit_data_integrity.py` | `core/sqlite_loader.py` | `core/loaders/sqlite_loader.py` |

## 4. Hardcoded Language Arrays (8 Files)
The following files contain `['pl', 'de']` or `['de', 'pl']` and are identified as "Non-Universal" technical debt. They are not strictly broken by the *move*, but are part of the audit.

1. `tools/enrich_neo4j_titles.py`
2. `tools/inspect_neo4j.py`
3. `tools/verify_edge_direction.py`
4. `tools/update_sqlite_schema.py`
5. `tools/audit_data_integrity.py`
6. `tests/validate_gate_5b1.py`
7. `tests/validate_gate_5a3.py`
8. `tests/validate_data_structure.py`

## 5. Shell Script Refactoring
- `dev.sh`: **CLEAN**. Contains no references to `core/tools`.

## 6. Rollback Strategy
If migration fails:
1. Move files back to original locations using `git restore`.
2. Revert text replacements in the files listed above.
3. Verify integrity using `tests/validate_all_accessors.py`.