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
