# WikiGraph

WikiGraph is a tool designed to process Wikipedia database dumps and convert them into a knowledge graph using Neo4j for topology and SQLite for metadata storage. It allows for offline analysis, pathfinding, and visualization of Wikipedia's link structure.

## Overview

The system supports multiple languages (currently **Polish** and **German**) by running isolated Neo4j instances via Docker. It handles the full ETL pipeline: downloading raw SQL dumps, parsing them, resolving redirects, generating graph CSVs, and performing a bulk import into the database. A unified FastAPI backend orchestrates queries across these databases.

## Architecture

The project is structured as a set of services and a core processing pipeline:

```
┌─────────────────────────────────────────────────┐
│            Unified Backend API (FastAPI)         │
│  (Routes: /api/pl/... → localhost:7474)         │
│  (Routes: /api/de/... → localhost:7475)         │
└─────────────────────────────────────────────────┘
                    ↓
┌──────────────┐      ┌──────────────┐
│ Docker       │      │ Docker       │
│ Container    │      │ Container    │
│ neo4j-pl     │      │ neo4j-de     │
│ Port: 7474   │      │ Port: 7475   │
└──────────────┘      └──────────────┘
```

## Prerequisites

*   Docker & Docker Compose
*   Python 3.10+
*   Node.js 18+

## Setup and Usage

### Quick Start

To start the environment for a specific language (e.g., Polish):

```bash
./dev.sh start pl
```

To start all languages:

```bash
./dev.sh start all
```

To check the status of services:

```bash
./dev.sh status
```

### Import Pipeline

To process a new language (e.g., German), execute the pipeline scripts in the following order:

1.  **Download Data:** Fetches the required SQL dumps from Wikimedia.
    ```bash
    python3 core/tools/fetch_sql_dumps.py de
    ```

2.  **Metadata Ingestion:** Parses SQL dumps and populates the SQLite database.
    ```bash
    python3 core/sqlite_loader.py --init --lang de
    ```

3.  **Topology Generation:** Extracts the link graph and generates import-ready CSV files.
    ```bash
    python3 core/tools/prepare_neo4j_csv.py --lang de
    ```

4.  **Bulk Import:** Loads the CSV files into the Neo4j container.
    ```bash
    bash core/tools/run_neo4j_import.sh de
    ```

## Project Structure

*   `core/`: Core ETL logic, parsers, and processing scripts.
*   `app/`: FastAPI backend service.
    *   `app/core/`: Configuration and logging.
    *   `app/services/`: Database connection managers.
    *   `app/api/routers/`: API endpoints.
*   `frontend/`: Next.js visualization interface.
*   `config/`: Configuration for infrastructure and language-specific parsing rules.
*   `data/`: Directory for raw dumps, SQLite databases, and Neo4j volume data (not versioned).
*   `tools/`: Verification and maintenance scripts.

## Data Validation

The project employs validation steps at key stages of the pipeline:
*   **Gate 1-3:** Data Ingestion Integrity.
*   **Gate 4:** Pre-Import Safety Checks.
*   **Gate 5:** Post-Import Graph Verification (Connectivity, Integrity).
*   **Gate 5A:** Backend Integration & Health Checks.

## License

GPLv3
