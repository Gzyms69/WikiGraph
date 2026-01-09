# WikiGraph Knowledge Engine

WikiGraph is a graph-based system designed to visualize and analyze the semantic structure of Wikipedia. It transforms raw Wikipedia dumps into a Neo4j graph database, allowing for the exploration of interconnected concepts across multiple languages.

## Project Overview

The system consists of three main components:
1.  **Data Pipeline:** Python scripts that parse Wikipedia XML/SQL dumps and ingest them into Neo4j.
2.  **Backend API:** A FastAPI service that exposes graph algorithms (PageRank, Shortest Path, Hybrid Ranking) via REST endpoints.
3.  **Frontend Visualization:** A Next.js/React application using `react-force-graph-3d` to render the knowledge nebula in a browser.

## Key Features

### Hybrid Weighted Ranking
WikiGraph uses a sophisticated ranking engine to determine the most relevant neighbors for any given concept. Instead of relying on a single metric, it blends three distinct algorithms:
*   **Jaccard Similarity:** Measures direct structural overlap (shared neighbors). Useful for finding strict synonyms.
*   **Adamic-Adar:** Weights connections by the rarity of the shared neighbors. Excellent for finding specific, meaningful context.
*   **PageRank (Global & Personalized):** Measures the global influence of a node.

Users can adjust the weights of these algorithms in real-time via the "System Settings" panel in the frontend to tailor the discovery process (e.g., favoring global fame vs. niche relevance).

### Interlingual Concept Mapping
Nodes in the graph represent "Concepts" (identified by Wikidata QIDs), which are language-agnostic. These Concepts are linked to language-specific "Articles" (e.g., English, Polish, German). This allows the graph to be traversed seamlessly across language barriers.

## Architecture

*   **Database:** Neo4j (Graph Database)
*   **Backend:** Python 3.12, FastAPI, Neo4j Driver, GDS (Graph Data Science) Library
*   **Frontend:** TypeScript, Next.js 14, Tailwind CSS, Three.js
*   **Infrastructure:** Docker & Docker Compose

## Quick Start

The project is managed by a central control script: `dev.sh`.

### Prerequisites
*   Docker and Docker Compose
*   Python 3.10 or higher
*   Node.js 18 or higher

### Running the System
To start the entire stack (Database, API, and Frontend):

```bash
./dev.sh start
```

This command will:
1.  Start the Neo4j container.
2.  Wait for the database to be ready.
3.  Start the FastAPI backend on port 8000.
4.  Start the Next.js frontend on port 3000.

### Accessing Services
*   **Frontend:** http://localhost:3000
*   **API Documentation:** http://localhost:8000/docs
*   **Neo4j Browser:** http://localhost:7474 (Default credentials: neo4j/wikigraph)

### Stopping the System
To stop the backend and frontend processes (leaves Neo4j running):

```bash
./dev.sh stop
```

To stop everything and remove containers (data in `data/neo4j_data` is preserved):

```bash
./dev.sh clean
```

## Usage Guide

1.  **Exploration:** Open the frontend. You will see a 3D visualization of the graph.
2.  **Search:** Use the search bar (top right) to find specific articles (e.g., "Kielce", "Python").
3.  **Navigation:** Click on a node to focus on it. This triggers the Weighted Hybrid Ranking engine to fetch and display its most relevant neighbors.
4.  **System Settings:**
    *   Click the "Settings" gear icon in the bottom control deck.
    *   **Algorithm Weights:** Adjust the sliders to change how neighbors are ranked. For example, increase "Adamic-Adar" to find more specific connections.
    *   **Physics:** Tune the gravity and link distance to change the layout of the 3D nebula.
    *   **Regenerate Knowledge:** Click this button to re-calculate connections for all currently visible nodes using your new weight settings.

## Data Ingestion

To populate the graph with new data:
1.  Place processed CSV files in `data/neo4j_bulk/`.
2.  Run `./dev.sh import` to trigger the bulk importer. **Warning:** This will wipe the current database.

## Development

*   **Backend Code:** Located in `app/`. The main graph logic is in `app/routers/graph.py`.
*   **Frontend Code:** Located in `frontend/src/`. The main visualization component is `WikiNebula.tsx`.
*   **Tools:** The `tools/` directory contains scripts for verifying algorithms and debugging the graph structure.