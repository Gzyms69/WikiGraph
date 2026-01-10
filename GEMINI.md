# WikiGraph: Project Context

## Purpose
WikiGraph is a system designed to process Wikipedia data (dumps) and build a large-scale graph representation (likely in Neo4j) to enable advanced queries like shortest path analysis between articles.

## Architecture & Key Technologies
- **Backend:** Python (FastAPI suggested by `run_api.py`)
- **Graph Database:** Neo4j (indicated by `core/engine/graph_engine.py` and `data/neo4j_data`)
- **Relational Database:** SQLite (indicated by `core/sqlite_loader.py`)
- **Data Processing:** Specialized tools for parsing Wikipedia XML/SQL dumps and cleaning import data.

## Key Files & Directories
- `app/`: API implementation (`api.py`, `models.py`).
- `core/`: Core logic for data ingestion, parsing, and graph management.
- `core/engine/`: Neo4j schema setup and engine logic.
- `data/`: Raw and processed Wikipedia data.
- `tools/`: CLI tools for monitoring and graph verification.

## Project Conventions
- Uses `requirements.txt` for dependency management.
- Includes a `setup_environment.sh` for initialization.
- Uses a `PROJECT_STATUS.md` to track progress (a custom convention for this project).

## Multilingual Wikipedia Strategy (Critical)

To ensure the system is truly language-agnostic, we must handle structural differences in Wikipedia data sources. Code **must not** hardcode "pl" or "en" defaults.

### 1. Parsing Differences
Languages differ in structural keywords. The `core/parser.py` relies on `config/language_manager.py` to provide these.

| Feature | English | Polish | German | Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **Namespace** | `Category:` | `Kategoria:` | `Kategorie:` | Use `siteinfo` to fetch local alias. |
| **Redirect** | `#REDIRECT` | `#PATRZ`, `#PRZEKIERUJ` | `#WEITERLEITUNG` | Check against list of magic words. |
| **File** | `File:`, `Image:` | `Plik:`, `Grafika:` | `Datei:` | Use `siteinfo` namespaces. |
| **Date Format** | `May 14, 2024` | `14 maja 2024` | `14. Mai 2024` | Use locale-specific parsers if extracting dates. |

### 2. Configuration Architecture
Currently, the system uses static YAML files in `config/languages/` (`pl.yaml`, `de.yaml`).
**Limitation:** This does not scale to all 300+ languages.
**Solution:** We need an `auto_config.py` tool.

### 3. Roadmap to Infinite Scalability
- [ ] **Dynamic Config Generator:** Create `core/tools/fetch_lang_config.py` to query `https://{lang}.wikipedia.org/w/api.php?action=query&meta=siteinfo` and generate the YAML automatically.
- [ ] **Universal Parser:** Ensure `core/parser.py` loads this dynamic config.
- [ ] **Date Normalization:** Implement a strategy (e.g., `dateparser` library) to handle locale-specific date strings if extraction is required.

### 4. Implementation Rules
1.  **Never** iterate a hardcoded list `['pl', 'de']`. Use `data/raw` file scanning.
2.  **Never** assume `Category:` is the prefix. Use `LanguageManager.get_namespace_prefixes(lang)`.
3.  **Always** fail gracefully if a language config is missing (or attempt to fetch it).