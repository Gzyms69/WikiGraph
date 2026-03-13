# WikiGraph Rebuild Plan: Hybrid, Multi-Source Knowledge Graph Lab

##  Progress Tracker (Updated: 2026-02-11)
*   **Protocol:** Adopted "Fail-Safe" pipeline with strict validation gates.
*   **Phase 6 Complete:** Core Graph Engine Restoration.
*   **Current Status: Phase 7 Complete (3D Visualizer Integration).**
    *   **Stabilization Audit:** Fixed system-ending 32GB RAM crash caused by workspace root resolution loops.
    *   **Isolation:** Frontend decoupled from root data directories to prevent recursive build scanning.
    *   **CORS:** Implemented backend middleware to enable secure browser-to-API communication.
*   **Next Phase: Phase 8 Active (Hybrid AI Engine).**

## 1. Comprehensive Legacy Feature Audit (The "Gold Standard")

We must eventually restore these features from the legacy codebase (`legacy/backend_old/routers/`).

### 1.1. Graph Topology & Traversal (`graph.py`)
*   **Weighted Neighbors (`/weighted-neighbors`):**
    *   **Logic:** Calculates neighbor relevance using a weighted sum of **Jaccard Coefficient**, **Adamic-Adar Index**, and **Personalized PageRank**.
    *   **Normalization:** Min-Max normalization of scores within the candidate set.
    *   **Filtering:** Excluded "List of", "Category:", etc.
*   **Shortest Path (`/shortest-path`):**
    *   **Logic:** Standard Neo4j `shortestPath` (BFS).
    *   **Feature:** Handled Start==End edge case.
*   **Nebula Sample (`/nebula`):**
    *   **Logic:** Fetched top PageRank nodes per language to create a "Universe" visualization.
    *   **Feature:** Balanced sampling (e.g., 50 PL, 50 DE).
*   **Languages (`/languages`):** Listed available datasets.

### 1.2. Network Analytics (`analytics.py`)
These features used the Neo4j Graph Data Science (GDS) library.
*   **PageRank (`/pagerank`):** Global influence scoring.
*   **Bridges (`/bridges`):** Used **Betweenness Centrality** to find nodes connecting clusters.
*   **Silos (`/silos`):** Used **Louvain Modularity** to find isolated communities.
*   **K-Core (`/k-core`):** Decomposed graph shells to find the dense core.
*   **Cross-Lingual Gaps (`/gaps`):** Found high-degree nodes in Lang A missing in Lang B.

### 1.3. Search & ML
*   **Keyword Search (`/search/keyword`):** Full-text Lucene index on `Article.title`.
*   **Embeddings (`/ml/embeddings`):** FastRP (Random Projection) node embeddings (16-dim).

### 1.4. Frontend Features (`frontend/`)
*   **Visual Engine:** `3d-force-graph` (Three.js) rendering.
*   **Control Deck:** Search, Language Toggle, Algorithm Weight Sliders (Jaccard/AA/PPR).
*   **Node Details:** Slide-out panel with abstract and metadata.

---

## 2. Revised System Architecture (Virtual Bridge)

The Unified Backend API acts as a **Virtual Bridge**, federating queries across isolated language databases. It does not maintain its own state but orchestrates parallel queries to Neo4j containers and SQLite databases.

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Frontend (Next.js)                         │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ HTTP/JSON
┌───────────────────────────────▼─────────────────────────────────────┐
│                     FastAPI Backend Service (Unified API)           │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                     Graph Query Engine                       │   │
│  │  ┌─────────────┐                            ┌─────────────┐  │   │
│  │  │  Lang Router│───────────────────────────►│   WDQS      │  │   │
│  │  └──────┬──────┘                            │   Adapter   │  │   │
│  └─────────┼───────────────────────────────────└─────────────┘  │   │
│            │                                                    │   │
│   ┌────────▼────────┐    ┌─────────────────┐                    │   │
│   │  Neo4j (PL)     │    │   Neo4j (DE)    │                    │   │
│   │ Port: 7474/7687 │    │ Port: 7475/7688 │                    │   │
│   └────────┬────────┘    └────────┬────────┘                    │   │
└────────────┼──────────────────────┼─────────────────────────────┘   │
             │                      │                                 │
        ┌────▼────┐            ┌────▼────┐                            │
        │  SQLite │            │  SQLite │                            │
        │  pl.db  │            │  de.db  │                            │
        └─────────┘            └─────────┘                            │
```

### 2.1 Backend Components
*   **Core (`app/core/`):** Loads `infrastructure.yaml` to discover available languages and ports. Centralized logging.
*   **Services (`app/services/`):**
    *   **Neo4jManager:** Singleton connection pool. Handles **Graceful Degradation** (if 'de' is down, 'pl' still works). Resolves routing.
    *   **MetadataManager:** Connects to SQLite for rich content (Titles, Infoboxes).
*   **Routers (`app/api/routers/`):**
    *   **Health (`/health`):** Aggregates status.
    *   **Unified (`/api/unified`):** The Virtual Bridge. Broadcasts queries by QID and merges results.

### 2.2 Data Flow (Example: Node Lookup)
1.  **Request:** `GET /api/unified/node/Q36`
2.  **Router:** Calls `Neo4jManager.broadcast("MATCH ... {qid: 'Q36'} ...")`
3.  **Manager:** Spawns async tasks for `pl` (Port 7687) and `de` (Port 7688).
4.  **Result:** Merges responses by QID.
5.  **Enrichment:** Router calls `MetadataManager` to fetch titles/infoboxes from `pl.db` and `de.db`.
6.  **Response:** JSON with combined data.

### 2.3 Cross-Language Traversal Algorithm (BFS)
To explore the graph across languages, we use a **Level-Synchronous Breadth-First Search (BFS)**:

*   **Logic:**
    *   Maintain `visited` set of QIDs.
    *   For each depth level, broadcast query to ALL active language DBs.
    *   Merge neighbors into `next_frontier`.
    *   Trim frontier to `limit_per_depth` (e.g., 50) to prevent explosion.
*   **Safety Limits:** Max Depth: 3, Max Nodes: 1000.
*   **Timeout:** 3s per language query.

---

## 3. Phased Implementation Plan (Revised)

**Phase 4A: Multi-Language Infrastructure (Complete)**
*   [x] Create `config/infrastructure.yaml`.
*   [x] Refactor `dev.sh`.
*   [x] **German Import:** Download, Ingest, Topology, Import.

**Phase 5: Unified Backend API (Complete)**
*   [x] **Gate 5A.1:** Backend Skeleton & Config.
*   [x] **Gate 5A.2:** Connection Manager & Degradation.
*   [x] **Gate 5A.3:** Health Endpoint.
*   [x] **Gate 5B.1:** QID Endpoints (Merged).
*   [x] **Gate 5B.2:** Language Endpoints (Pathfinding).
*   [x] **Gate 5B.3:** Cross-Language Traversal (BFS).
*   [x] **Gate 5B.5:** Metadata Enrichment (Infoboxes for PL/DE).

**Phase 6: API Restoration & Search (Complete)**
*   [x] **Gate 6.1:** Refactor API to serve enriched Infobox data (JSON).
*   [x] **Gate 6.2:** Keyword Search (Re-implement Lucene/Text index or FTS).
*   [x] **Gate 6.3:** Weighted Neighbors (Port Jaccard/AA logic).

### Phase 7: AI & Vector Search (Planned)
*   [ ] **Gate 7.1:** ChromaDB Integration (Vector Store).
*   [ ] **Gate 7.2:** Embedding Pipeline (Sentence Transformers).
*   [ ] **Gate 7.3:** Semantic Search Endpoint.
*   [ ] **Gate 7.4:** RAG Context Generation.

## 4. Architectural Principle: Minimal Neo4j (Gate 5B.3.9)

**Decision (Jan 2026):** Neo4j must remain lean to maximize graph traversal performance and minimize memory footprint. Metadata should reside in SQLite.

*   **Neo4j:** Stores ONLY graph topology (Nodes `QID` and Relationships `LINKS_TO`).
*   **SQLite:** Stores ALL node attributes (`title`, `out_degree`, `in_degree`, `infobox`, `text`).

## Fast Track Sprint: Recruiter-Ready MVP (February 2026)

### Phase 7: The Visualizer (Sprint Week 1)
*   [ ] **Gate 7.1:** Legacy Frontend Cleanup. Remove complex UI elements and unused components.
*   [ ] **Gate 7.2:** API Integration. Wire Frontend Search to `/api/v1/search` and Graph View to `/api/v1/entity`.
*   [ ] **Gate 7.3:** 3D Visualization. Restore `3d-force-graph` rendering for live topological data.

### Phase 8: Cloud AI Integration (Sprint Week 2)
*   [ ] **Gate 8.1:** Provider Pattern. Implement `AIService` architecture in the backend.
*   [ ] **Gate 8.2:** Gemini Integration. Implement `GeminiCloudProvider` using Google AI SDK.
*   [ ] **Gate 8.3:** Insight Feature. Create `/api/v1/ai/insight` and the frontend "AI Summary" card.
