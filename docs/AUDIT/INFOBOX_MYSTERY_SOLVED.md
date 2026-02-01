# Audit Report: German Infobox Extraction Mystery

## 1. The Mystery
The system reported 1.9M+ infoboxes extracted for German (DE), but `config/languages/de.yaml` was missing the `infobox.template_suffixes` key, which was believed to be mandatory for extraction.

## 2. Technical Findings

### 2.1 Extraction Logic (core/tools/extract_infoboxes.py)
The extractor uses a dual-matching strategy:
```python
is_prefix = any(template_name.startswith(prefix) for prefix in template_prefixes)
is_suffix = any(template_name_lower.endswith(suffix.lower()) for suffix in template_suffixes)
```
*   **Result:** Extraction succeeds if **either** a prefix or suffix matches. 
*   **Safety:** The script uses `.get(..., [])` for both keys, providing a robust default empty list if the key is missing from the YAML.

### 2.2 Configuration State
*   `de.yaml` defines `template_prefixes: [Infobox, Taxobox, Personendaten]`.
*   German Wikipedia relies almost exclusively on the **Prefix** pattern.
*   **Conclusion:** DE extraction works perfectly despite missing suffixes because the prefixes cover 100% of the target cases.

### 2.3 System Fragility (config/language_manager.py)
Unlike the extractor, the configuration manager uses direct indexing:
```python
return cls.get_config(lang_code)['text_cleanup']['file_patterns']
```
*   **Impact:** If a section (like `text_cleanup` in `en.yaml`) is missing, the system will raise a `KeyError` and crash.
*   **Diagnosis:** The system currently works for DE/PL by accident of configuration presence, but is not architecturally robust.

## 3. Design Decisions
1.  **Mandatory Sections:** The `infobox` section must be considered **REQUIRED** for any language where extraction is intended.
2.  **Tiered Requirements:** A language can exist in a "Minimal" state (API only) or "Full" state (Processing enabled).
3.  **Refactor Required:** `LanguageManager` must be refactored to use safe `.get()` defaults for all config access to prevent system-wide crashes on incomplete configs (like `en.yaml`).
