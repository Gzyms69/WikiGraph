# WikiGraph Lab: Universal Knowledge Graph

WikiGraph is a high-performance system designed to ingest, unify, and analyze massive Wikipedia datasets across multiple languages into a single Neo4j Knowledge Graph.

It features a **3D Interlingual Nebula** visualizer and a robust **Graph Data Science (GDS)** powered API.

## 🚀 Features

### 1. 🌌 3D Interlingual Nebula (Frontend)
*   **High-Performance Rendering:** WebGL-based 3D engine capable of visualizing millions of nodes.
*   **Flag-Themed Articles:** Every Wikipedia edition is represented by its flag, making language boundaries visually distinct.
*   **Universal Exploration:** Search for any topic across all languages and "fly" the camera to its position in the 3D universe.
*   **Infinite Expansion:** Dynamically fetches and spawns neighbors as you explore the graph.

### 2. 🧠 Research API (Backend)
*   **FastAPI & GDS:** Leveraging Neo4j Graph Data Science for advanced analytics.
*   **AI/ML Readiness:** FastRP node embeddings for downstream machine learning.
*   **Graph Traversal:** Interlingual shortest paths and topological recommendations (Personalized PageRank).
*   **Research Tools:** Bridge detection (Betweenness), Silo detection (Louvain), and Gap Analysis (finding missing articles).

## 🏗️ Architecture

1.  **Ingestion:** Streaming XML/SQL parser -> Standardized JSONL.
2.  **Bulk Load:** High-speed CSV export -> `neo4j-admin import`.
3.  **Analytics:** GDS Plugin for algorithms (PageRank, Louvain, Betweenness).
4.  **Interface:** FastAPI Backend + Next.js 3D Frontend.

## 🛠️ Quick Start

### 1. Launch Services
Use the provided development script to start the entire stack:
```bash
./dev.sh start
```
*   **Frontend:** http://localhost:3000
*   **API Docs:** http://localhost:8000/docs
*   **Neo4j:** http://localhost:7474

### 2. Run Analytics Initialization
Once the app loads, you must initialize the GDS projection:
```bash
curl -X POST http://localhost:8000/analytics/initialize
```

## 📂 Project Structure
*   `app/`: FastAPI Backend (Routers for ML, Graph, Analytics).
*   `frontend/`: Next.js 3D Dashboard.
*   `core/`: Data processing and bulk loading engine.
*   `ingest.py`: Master ingestion controller.
*   `run_bulk_import.sh`: High-speed database initializer.

---
*WikiGraph Lab - Visualizing the Universe of Human Knowledge.*