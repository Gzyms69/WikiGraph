# Audit Report: Phase 6 (Testing Layer)

## 1. Hardcoded String Quantification
**Status:** ❌ **CRITICAL FAILURE**

Grep results confirm massive brittleness:
-   `grep "de"` returned **26 test/tool files**.
-   `grep "pl"` returned **26 test/tool files**.

**Key Offenders:**
-   `tests/validate_data_structure.py`: `if lang == 'de' or qid == "Q36"`.
-   `tests/smoke_test_api.py`: Hardcoded list `[("Q64", "de"), ("Q1744", "pl")]`.
-   `tests/validate_api_infobox_perf.py`: `benchmark_lang('de')`, `benchmark_lang('pl')`.

**Impact:**
-   If we add `es`, **NONE** of these tests will cover it automatically.
-   Adding Spanish requires manually updating ~26 files to add `benchmark_lang('es')`.

## 2. Logic Inspection (`tests/validate_data_structure.py`)
**Status:** ❌ **ANTI-PATTERN**

Code snippet:
```python
async def main():
    for lang in ["pl", "de"]:  # <--- HARDCODED LIST
        results = await validate_neo4j_structure(lang)
```
This test manually iterates a fixed list instead of importing `settings`.

## 3. Findings & Remediation

| ID | Type | Description | Remediation |
| :--- | :--- | :--- | :--- |
| T-01 | **CRITICAL** | Tests iterate `["pl", "de"]` manually. | Replace with `for lang in settings['languages'].keys():`. |
| T-02 | **MAJOR** | Test data (QIDs) is hardcoded for DE/PL. | Move test data to `tests/fixtures/{lang}.json`. |
| T-03 | **MINOR** | "Golden QIDs" (Berlin/Madonna) are specific to DE/PL. | We need "Golden QIDs" for every supported language (e.g., Madrid for ES). |

## 4. Conclusion
The Testing Layer is **Not Language Agnostic**. It is strictly a "Bi-lingual Verification Suite". While the Core System is ready for Spanish, we cannot *prove* it works without rewriting the tests.
