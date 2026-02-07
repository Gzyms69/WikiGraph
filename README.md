# WikiGraph

**Current Status (February 7, 2026):**
- **Phase 1 COMPLETE:** Hardened Search, Rosetta Comparison, and Scored Neighbors are live.
- **Enrichment:** Dual-language metadata (3.2M records) with FTS5 indexing.
- **Multi-Lang:** PL, DE, and ES (Spanish) fully processed and active.

**For latest details:** See `PROJECT_STATUS.md`, `APIPLAN.md` and `devlog.md`.

WikiGraph is a language-agnostic tool designed to process Wikipedia database dumps and convert them into a knowledge graph using Neo4j for topology and SQLite for metadata storage. It allows for offline analysis, pathfinding, and visualization of Wikipedia's link structure for any configured language.

## Overview

The system supports multiple languages by running isolated Neo4j instances via Docker. It handles the full ETL pipeline: downloading raw SQL dumps, parsing them, resolving redirects, generating graph CSVs, and performing a bulk import into the database. A unified FastAPI backend orchestrates queries across these databases dynamically.

## Architecture

The project is structured as a set of services and a core processing pipeline. The backend routes requests to the appropriate language container based on the URL path.

```
┌─────────────────────────────────────────────────┐
│            Unified Backend API (FastAPI)         │
│  (Routes: /api/{lang}/... → neo4j-{lang}:7474)  │
└─────────────────────────────────────────────────┘
                    ↓
┌──────────────┐      ┌──────────────┐
│ Docker       │      │ Docker       │
│ Container    │      │ Container    │
│ neo4j-{lang} │      │ neo4j-{lang} │
└──────────────┘      └──────────────┘
```

## Data Model

The system uses a dual-database architecture optimized for performance and memory efficiency:

### 1. Neo4j (Graph Topology)
*   **Purpose:** Stores *only* the graph structure (Nodes & Edges) for fast traversal.
*   **Nodes:** Label `:Concept`
    *   `qid`: Wikidata ID (e.g., Q36) - **Primary Key**
    *   `ns`: Namespace (0 for articles)
    *   *(Note: No Titles or Metadata)*
*   **Relationships:** Type `:LINKS_TO`
    *   Directional link between Concepts.

### 2. SQLite (Metadata & Content)
*   **Purpose:** Stores rich metadata, titles, text, and computed statistics.
*   **Search:** Includes **FTS5 Virtual Tables** (`articles_fts`) for sub-millisecond keyword matching.
*   **Tables:**
    *   `pages`: Page metadata. Columns:
        *   `page_id`, `title`, `namespace`, `len`
        *   `out_degree`, `in_degree` (Pre-calculated graph metrics)
        *   `infobox`: JSON field storing extracted structured data (e.g., birth dates, coordinates).
    *   `id_mapping`: Maps `page_id` to `qid`.
    *   `link_targets`: Raw target strings from dumps.
    *   `category_links`: Category hierarchy (if imported).
    *   **`articles_fts`**: FTS5 table for title indexing.

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

To start all configured languages:

```bash
./dev.sh start all
```

To check the status of services:

```bash
./dev.sh status
```

### Import Pipeline

To process a new language (e.g., German 'de' or Spanish 'es'), execute the pipeline scripts:

1.  **Download Data:** Fetches the required SQL dumps from Wikimedia.
    ```bash
    python3 core/pipeline/fetch_sql_dumps.py <lang_code>
    ```

2.  **Metadata Ingestion:** Parses SQL dumps and populates the SQLite database.
    ```bash
    python3 core/loaders/sqlite_loader.py --init --lang <lang_code>
    ```

3.  **Topology Generation:** Extracts the link graph and generates import-ready CSV files.
    ```bash
    python3 core/pipeline/prepare_neo4j_csv.py --lang <lang_code>
    ```

4.  **Bulk Import:** Loads the CSV files into the Neo4j container.
    ```bash
    bash core/pipeline/run_neo4j_import.sh <lang_code>
    ```

## Project Structure

*   `core/`: Core ETL logic.
    *   `pipeline/`: Orchestration scripts (Download, CSV Prep, Import).
    *   `loaders/`: Data parsers and SQLite loaders.
    *   `engine/`: Neo4j interaction logic.
    *   `legacy/`: Archived tools.
*   `tools/`: Helper scripts.
    *   `ops/`: Infrastructure management (Docker, Containers).
    *   `analytics/`: Data analysis and metric computation.
    *   `archive/`: One-off debug scripts.
*   `app/`: FastAPI backend service.
*   `config/`: Configuration for infrastructure and language-specific parsing rules.
*   `data/`: Directory for raw dumps, SQLite databases, and Neo4j volume data.
*   `tests/`: Verification suites.
    *   `unit/`: Isolated module tests.
    *   `integration/`: End-to-end API and container tests.

## Data Validation

The project employs validation steps at key stages of the pipeline:
*   **Gate 1-3:** Data Ingestion Integrity.
*   **Gate 4:** Pre-Import Safety Checks.
*   **Gate 5:** Post-Import Graph Verification (Connectivity, Integrity).
*   **Gate 5A:** Backend Integration & Health Checks.
*   **Phase 1 Hardening:** QID Regex Validation, Connection Pooling (SQLAlchemy), Lifecycle Management (Lifespan), and FTS Syntax Robustness.

## License

GPLv3
