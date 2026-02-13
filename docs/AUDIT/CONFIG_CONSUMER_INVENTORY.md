# Config Consumer Inventory (Phase 5.1 Audit)

This document maps every configuration key consumed by the WikiGraph codebase and identifies the safety of its access pattern.

## 1. Configuration Key Inventory

| Key Path | Consumer(s) | Default Value (if missing) | Safety Level |
| :--- | :--- | :--- | :--- |
| `wikipedia.dbname` | `parser.py`, `LanguageManager` | **None (Required)** | 🔴 **UNSAFE** (Strictly enforced) |
| `wikipedia.redirect_keywords` | `parser.py` | `[]` | 🔴 **UNSAFE** (Direct dict access) |
| `wikipedia.namespace_prefixes` | `parser.py` | `[]` (for category) | 🟡 **PARTIAL** (Uses `.get()`) |
| `infobox.template_prefixes` | `extract_infoboxes.py` | `[]` | 🔴 **UNSAFE** (Direct dict access) |
| `infobox.template_suffixes` | `extract_infoboxes.py` | `[]` | 🔴 **UNSAFE** (Direct dict access) |
| `infobox.parameter_map` | `extract_infoboxes.py` | `{}` | 🔴 **UNSAFE** (Direct dict access) |
| `text_processing.has_spaces` | `parser.py` | `True` | ✅ **SAFE** (Uses `.get()`) |
| `text_cleanup.file_patterns` | `LanguageManager` | `[]` | ✅ **SAFE** (Accessor implemented) |
| `language.*` | `LanguageManager` | Code/Code/Code | ✅ **SAFE** (Accessor implemented) |
| `processing.enabled` | `LanguageManager` | `False` | ✅ **SAFE** (Accessor implemented) |

---

## 2. File-by-File Audit

### 2.1 Pipeline Orchestrator (`core/pipeline/ingest.py`)
- **LanguageManager Usage:** None.
- **Hardcoding:** High. Hardcodes the sequence of tools and instruction output.
- **Risk:** No config awareness. Cannot validate if a language is "importable" before starting.

### 2.2 XML Parser (`core/loaders/parser.py`)
- **LanguageManager Usage:** Direct `get_config()` call.
- **Access Pattern:** 
    - `config['wikipedia']['redirect_keywords']` (Will crash if `wikipedia` or `redirect_keywords` is missing).
- **Hardcoding:**
    - Infers XML/Index paths using `f'{dbname}-*-pages-articles-multistream.xml.bz2'`. This is a robust pattern but depends on a valid `dbname`.

### 2.3 Infobox Extractor (`core/pipeline/extract_infoboxes.py`)
- **LanguageManager Usage:** Direct `get_config()` call.
- **Access Pattern:** 
    - `config['infobox'].get('template_prefixes', [])` (Will crash if `infobox` section is missing).
- **Hardcoding:**
    - Path: `data/raw/{args.lang}wiki-latest-pages-articles-multistream.xml.bz2`.
    - Path: `data/db/{args.lang}.db`.

### 2.4 Graph Generator (`core/pipeline/prepare_neo4j_csv.py`)
- **LanguageManager Usage:** **NONE**.
- **Access Pattern:** N/A.
- **Hardcoding:**
    - **CRITICAL**: Hardcodes database path `data/db/{lang}.db`.
    - **CRITICAL**: Hardcodes dump path `data/raw/{lang}wiki-latest-pagelinks.sql.gz`.
    - **CRITICAL**: Hardcodes output path `data/neo4j_bulk/{lang}`.

### 2.5 SQLite Loader (`core/loaders/sqlite_loader.py`)
- **LanguageManager Usage:** **NONE**.
- **Access Pattern:** N/A.
- **Hardcoding:**
    - **CRITICAL**: Hardcodes database path `data/db/{args.lang}.db`.
    - **CRITICAL**: Hardcodes namespaces `[0, 14]`.
    - **CRITICAL**: Hardcodes Wikidata property name `wikibase_item`.

---

## 3. Infrastructure Audit

### 3.1 Control Script (`dev.sh`)
- **Hardcoded Languages**: `['pl', 'de']` in `stop_all` and `case` start.
- **Hardcoded Ports**: `7474`, `7687` (PL) and `7475`, `7688` (DE).
- **Risk**: Impossible to start a third language (e.g., `es`) without manual script modification.

### 3.2 Bulk Importer (`core/pipeline/run_neo4j_import.sh`)
- **Defaults**: Defaults to `pl`.
- **Hardcoding**: Assumes `dev.sh start` can be called per language (it currently cannot).

---

## 4. Summary of Safety Gaps

1.  **Direct Indexing**: Multiple scripts use `config['section']['key']`. If any section (e.g., `infobox`) is missing from a new language YAML, the entire pipeline crashes.
2.  **Manager Bypassing**: `prepare_neo4j_csv.py` and `sqlite_loader.py` don't use the `LanguageManager`. They "guess" file paths that might conflict with the `dbname` configured in the manager.
3.  **Path Fragility**: There is no central authority for where a language's files live. Every script rebuilds the string `data/db/{lang}.db`.
4.  **Static Infrastructure**: The system is physically limited to two languages by `dev.sh`.
