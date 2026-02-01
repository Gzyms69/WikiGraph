# Audit Report: Phase 2 (Extraction Pipeline)

## 1. `extract_infoboxes.py` Forensics
**Status:** ✅ **MOSTLY CLEAN**

-   **Config Usage:** `LanguageManager.get_config(args.lang)` is used.
-   **Prefixes/Suffixes:** Loaded from config (`config['infobox'].get('template_prefixes')`).
-   **Regex:** `quick_has_infobox` constructs regex dynamically from these lists.
-   **File Paths:** `data/raw/{lang}wiki...` and `data/db/{lang}.db`. Dynamic.
-   **Logic:** No hardcoded "Infobox" string found in logic.

**Minor Issue:**
-   `param_map` is loaded but logic for using it (`if p_name in param_map:`) assumes simple 1:1 mapping. If `es` requires complex mapping, this might be too simple, but it is technically language agnostic.

## 2. `ingest.py` Forensics
**Status:** ✅ **CLEAN**

-   **Argument Passing:** Accepts `--lang` and passes it down to sub-scripts.
-   **Dynamic Paths:** Does not verify if `lang` is valid, just passes it. This relies on sub-scripts to fail if config missing.

## 3. Grep Analysis (Hardcoded Strings)
**Status:** ⚠️ **WARNING**

We found hardcoded language checks in **Tools** and **Tests**, but *not* in the Core Pipeline.

**Violations in `tools/` (Maintenance Scripts):**
-   `tools/verify_neo4j_graph.py`: Hardcoded `EXPECTED_NODES_PL`, `if lang == 'pl'`.
-   `tools/enrich_neo4j_titles.py`: `f"data/db/{'pl' if lang == 'pl' else 'de'}.db"` <-- **UGLY HACK**. This will break for `es`.
-   `tools/validate_infobox_extraction.py`: `if lang == 'de'`.

**Impact:**
-   The **Core Pipeline** (Ingest -> SQLite -> Extract -> CSV) supports `es`.
-   The **Verification Suite** (Audit tools) will **FAIL** for `es`.

## 4. Findings & Remediation

| ID | Type | Description | Remediation |
| :--- | :--- | :--- | :--- |
| E-01 | **MINOR** | `tools/enrich_neo4j_titles.py` has ternary hardcoded path. | Replace with `f"data/db/{lang}.db"`. |
| E-02 | **MINOR** | Verification tools contain hardcoded baselines. | Move baselines to a `tests/baselines/{lang}.json` file or make generic. |

## 5. Conclusion
The "Core Risk" (Extraction) is surprisingly robust. It respects `LanguageManager`. The system *can* ingest Spanish data today. The problem is we can't *verify* it because our test tools are hardcoded.
