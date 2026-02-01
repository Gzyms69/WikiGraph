# LanguageManager Refactor Plan

## 1. Objective
Refactor `core/config/language_manager.py` to support the **Two-Tier Configuration Schema** (Metadata vs. Processing) and eliminate crash risks from missing keys (specifically the `en.yaml` timebomb).

## 2. Current Flaws
1.  **Direct Indexing:** `cls.get_config(lang)['text_cleanup']` raises `KeyError` if section is missing.
2.  **No Defaults:** Assumes every config file has every key.
3.  **No Validation:** Loads any YAML without checking structure.

## 3. Refactor Strategy

### 3.1 Safe Accessor Pattern
Replace direct dictionary access with a robust `.get()` chain or a validated Pydantic model (Phase 2). For now (Phase 1), use deep defaults.

**New Method Signature:**
```python
def get_section(cls, lang_code: str, section: str, default: Any = None) -> Any:
    """Safe access to top-level sections with defaults."""
    cfg = cls.get_config(lang_code)
    return cfg.get(section, default)
```

### 3.2 Implemented Logic Changes

#### A. `get_text_cleanup_patterns(lang_code)`
*   **Old:** `return config['text_cleanup']['file_patterns']`
*   **New:**
    1.  Get `text_cleanup` section (default `{}`).
    2.  Get `file_patterns` key (default `[]`).
    3.  **Fallback:** If empty, return `namespace_prefixes['file']` (smart default).

#### B. `get_infobox_config(lang_code)`
*   **New Method:** Returns `{prefixes: [], suffixes: [], map: {}}`.
*   **Logic:**
    1.  Get `infobox` section.
    2.  If missing, check `processing.enabled`.
    3.  If enabled but missing -> Warning/Error.
    4.  If disabled -> Return empty safe structure.

### 3.3 Schema Validation (Validation Step)
Add a `validate_config(config)` method called on load.
*   **Check:** Does `language` exist? (Critical)
*   **Check:** Does `ui` exist? (Critical for API)
*   **Check:** If `processing.enabled`, do `wikipedia` and `infobox` exist?

## 4. Execution Steps (Implementation Phase)

1.  **Step 1:** Add `validate_config` method to `LanguageManager`.
2.  **Step 2:** Refactor all getter methods to use `.get()`.
3.  **Step 3:** Implement Smart Fallbacks (e.g., text cleanup defaults to file namespace).
4.  **Step 4:** Update `en.yaml` to include `processing: { enabled: false }` (Migration).

## 5. Success Metrics
*   `LanguageManager.get_text_cleanup_patterns('en')` returns `[]` (or default) instead of crashing.
*   `LanguageManager.get_infobox_config('de')` returns valid suffixes `[]`.
*   System successfully loads `es.yaml` (minimal config).
