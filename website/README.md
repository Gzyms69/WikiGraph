# WikiGraph Lab: Static Demo

This directory contains the **Static Demo** version of the WikiGraph frontend. 

## Purpose
Unlike the main `frontend/` application (which requires a running Python/Neo4j backend), this project is designed to be deployed as a standalone static site on **GitHub Pages**.

## Architecture: The "Iceberg Model"
To simulate the rich features of the full backend without a server, this demo uses an "Iceberg Model":
*   **Data:** A pre-computed JSON dataset (`src/demo-data/demo-nebula.json`) containing a curated subgraph of Wikipedia (Science, History, Art, etc.).
*   **Logic:** The `GraphService` (`src/utils/graphService.ts`) acts as a "Mock API". It queries the in-memory JSON to provide:
    *   **Search:** Fuzzy string matching.
    *   **Expansion:** Finding neighbors for a selected node.
    *   **Clustering:** Retrieving community data.

## Key Features
*   **3D Force Graph:** Powered by `react-force-graph-3d`.
*   **Interactive HUD:** Glassmorphism UI for search, details, and controls.
*   **Onboarding:** "How to Use" modal for new users.
*   **PageRank Visualization:** Node sizes reflect their importance score.

## Development
```bash
npm install
npm run dev
```

## Deployment
This project is configured for GitHub Pages.
```bash
npm run build
# The 'out' directory can be deployed
```
