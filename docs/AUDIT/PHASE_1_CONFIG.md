# Audit Report: Phase 1 (Configuration Layer)

## 1. Schema Consistency Analysis
**Status:** ⚠️ **MAJOR INCONSISTENCY**

Comparing `de.yaml`, `pl.yaml`, and `en.yaml`:

| Key Path | DE | PL | EN | Status |
| :--- | :--- | :--- | :--- | :--- |
| `language.code` | ✅ | ✅ | ✅ | Consistent |
| `wikipedia.namespace_prefixes` | ✅ | ✅ | ✅ | Consistent |
| `infobox.template_prefixes` | ✅ | ✅ | ✅ | Consistent |
| `infobox.template_suffixes` | ❌ Missing | ✅ Present | ❌ Missing | **Inconsistent** |
| `text_cleanup` | ✅ | ✅ | ❌ Missing | **Critical Gap** |
| `ui.interface_translations` | ✅ | ✅ | ✅ | Consistent |

**Impact:**
-   The extractor expects `template_suffixes` for PL. If run on DE/EN without checking for existence, it might crash or behave unexpectedly (Python `dict.get` returns `None` by default, but iteration might fail).
-   `en.yaml` is missing `text_cleanup`, which means English file links (`[[File:...]]`) might not be stripped correctly during text processing.

## 2. Hardcoded Values in Config
-   `de.yaml` defines `text_cleanup.file_patterns` using a YAML anchor `*id001`. This is valid YAML but brittle if the anchor moves.
-   `en.yaml` has a hardcoded `parameter_map: {}`. This implies we assume English keys are canonical. This is a valid assumption for English but requires documentation.

## 3. LanguageManager Forensics
**File:** `config/language_manager.py`

**Strengths:**
-   ✅ **JIT Configuration:** It attempts to run `fetch_lang_config.py` if a config is missing. This is a **HUGE WIN** for universality.
-   ✅ **Dynamic Loading:** Loads `*.yaml` files dynamically.

**Weaknesses:**
-   `get_processing_config` tries to access `config['processing']`.
    -   **Violation:** `processing` key **DOES NOT EXIST** in `de.yaml` or `pl.yaml`.
    -   **Impact:** `KeyError` if this method is ever called.
-   `get_text_cleanup_patterns` accesses `['text_cleanup']`.
    -   **Impact:** Will crash for `en.yaml` (key missing).

## 4. Findings & Remediation

| ID | Type | Description | Remediation |
| :--- | :--- | :--- | :--- |
| C-01 | **CRITICAL** | `LanguageManager.get_processing_config` accesses non-existent key `processing`. | Remove method or add default `processing` block to all YAMLs. |
| C-02 | **MAJOR** | `en.yaml` missing `text_cleanup` block. | Add `text_cleanup` to `en.yaml`. |
| C-03 | **MINOR** | Inconsistent `template_suffixes` key. | Ensure code uses `.get('template_suffixes', [])` safely. |

## 5. Answer to "Where does es.yaml come from?"
**Answer:** The `LanguageManager` has a built-in "JIT" (Just-In-Time) mechanism.
-   Line 47: `tool_path = root_dir / "core" / "tools" / "fetch_lang_config.py"`
-   Logic: If `es.yaml` is missing, it calls this script to fetch siteinfo from Wikipedia API and generate it.
-   **Verdict:** This is **TRUE Language Agnosticism** implemented correctly in code, but we must verify `fetch_lang_config.py` actually works and generates the correct schema.
