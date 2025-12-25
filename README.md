# WikiGraph 🚧

**Current Status:** 🔴 **BROKEN / UNDER REPAIR** 🔴

> **Developer Note (Dec 25, 2025):** 
> This tool is currently in a broken state. While the parsing logic exists, the primary database has been flagged as corrupted/broken. The Neo4j integration mentioned in previous documentation does not exist. Use this codebase for reference only; do not attempt to run it in a production environment.

## What is this?
WikiGraph is a Python-based tool designed to ingest massive Wikipedia XML dumps (specifically Polish and English), parse them into structured data, and serve them via a searchable API.

It uses a **streaming XML parser** to handle multi-gigabyte files with low memory footprint and stores the result in a **SQLite** database with Full-Text Search (FTS5) capabilities.

## The Honest Truth: What Works & What Doesn't

We believe in transparency. Here is the actual state of the project:

### ✅ What Works
- **Streaming Parser:** The `phase1_production.py` script successfully streams and parses huge XML dumps (tested on 2GB+ Polish wiki) without eating all your RAM.
- **SQLite Generation:** The loaders can populate a SQLite database with millions of articles and links.
- **Search API:** The Flask API (`api.py`) handles requests and performs full-text searches on the database.
- **Multilingual Structure:** The codebase is set up to handle multiple languages (currently configured for `pl` and `en`).

### ❌ What is Broken / Missing
- **The Database:** The `wikigraph_multilang.db` is currently considered **broken**. While it may open and show stats, data integrity issues render it unreliable for actual graph analysis.
- **Neo4j:** Previous documentation claimed Neo4j support. **This is false.** There is no graph database integration implemented yet.
- **English Data:** English Wikipedia support is experimental and currently stuck at a 1,000-article test set.
- **Frontend:** There is no user interface. It is a raw JSON API only.

## Project Structure

```text
WikiGraph/
├── app/                  # Flask API application
├── databases/            # SQLite storage (currently broken)
├── processed_batches/    # Intermediate JSONL/CSV files
├── raw_data_wiki/        # Place your XML dumps here
├── scripts/              # logic for parsing and loading
│   ├── phase1_production.py  # The main parser
│   ├── load_multilang_data.py# The DB loader
│   └── manage_db.py          # Database util (stats/init)
└── venv_linux/           # Python Virtual Environment
```

## Setup (If you want to try fixing it)

**Prerequisites:** Linux/WSL, Python 3.8+

1. **Activate Environment:**
   You must use the provided virtual environment.
   ```bash
   source venv_linux/bin/activate
   # OR run scripts directly:
   # ./venv_linux/bin/python3 scripts/manage_db.py stats
   ```

2. **Check Database Status:**
   ```bash
   python3 scripts/manage_db.py stats
   ```
   *Note: Even if this returns numbers, the DB is flagged as broken.*

3. **Run the API:**
   ```bash
   python3 run_api.py
   ```
   Server runs on `http://localhost:5000`.

## Key Commands

| Goal | Command | Status |
|------|---------|--------|
| **Parse Dump** | `python3 scripts/phase1_production.py` | ✅ Works |
| **Load DB** | `python3 scripts/load_multilang_data.py --lang=pl` | ⚠️ Unstable |
| **Search** | `curl "http://localhost:5000/api/search?q=Warszawa"` | ✅ Works (if DB loads) |
| **Health Check** | `curl http://localhost:5000/api/health` | ✅ Works |

## Roadmap to Recovery

1. **Fix Database Integrity:** Re-validate the foreign key relationships and schema consistency.
2. **Implement Neo4j:** Actually build the graph database connector for complex relationship analysis.
3. **Finish English Import:** Run the full pipeline for `enwiki`.
4. **Build UI:** Create the web frontend to visualize the graph.

---
*Maintained by Gzyms69. Last updated: Dec 2025.*