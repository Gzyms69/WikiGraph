# API Expansion Plan: WikiGraph Master Plan

**Status:** Phase 1 COMPLETED (Hardened)
**Architecture:** Minimal Neo4j (Topology/Compute) + Rich SQLite (Metadata/Metrics) + ChromaDB (Vectors)
**Philosophy:** A modular, high-performance Knowledge Engine offering Graph Theory, AI Search, and RAG capabilities.

---

## Phase 1: Foundations & Search (The "Retriever") - **COMPLETED**

**Goal:** Make the graph searchable via Keywords (FTS) and Concepts (Vectors).

### 1.1 Universal Search (SQLite FTS5) - [DONE]
*   **Endpoint:** `GET /api/v1/search/{lang}?q={query}`
*   **Implementation:** 
    - Uses SQLite **FTS5** virtual tables (`articles_fts`) for sub-millisecond prefix and keyword matching.
    - Query logic: `MATCH "{query}*"` (Prefix support).
    - Robustness: `try/except` wrapper prevents crash on malformed query syntax (e.g. unterminated quotes).

### 1.2 Vector Search (ChromaDB) - [PENDING]
*   **Infrastructure:** Integrate `chromadb` (Persistent Client) in `data/chroma`.
*   **Model:** `all-MiniLM-L6-v2` (via `sentence-transformers`).
*   **Pipeline:** `tools/ai/embed_articles.py` -> Batch processes SQLite articles -> Stores vectors in ChromaDB.
*   **Endpoint:** `GET /api/v1/search/{lang}?q={query}&type=semantic`

### 1.3 Infrastructure & Hardening - [DONE]
*   **Pooling:** Implemented `SQLAlchemy.QueuePool` in `app/services/sqlite_pool.py` for high-concurrency metadata fetching.
*   **Validation:** Strict QID regex validation (`^Q[0-9]+$`) on all routers.
*   **Lifecycle:** FastAPI `lifespan` manager handles clean disposal of SQLite and Neo4j connections.
*   **Health:** `GET /api/v1/health` provides real-time status of 6+ backend persistence layers.

### 1.4 The "Rosetta Stone" Comparison - [DONE]
*   **Endpoint:** `GET /api/v1/compare/{qid}?langs=pl,de,es`
*   **Implementation:** Parallel `asyncio.gather` fetch of metadata (Titles + Infoboxes) across specified SQLite databases.

---

## Phase 2: Core Graph Engine (The "Graph Mathematician") - **NEXT**

**Goal:** Provide deep structural insights using classical Graph Theory algorithms.
**Constraint:** Neo4j stores **ONLY** topology. All calculated metrics are stored in SQLite or computed on-the-fly.

### 2.1 Pathfinding (Navigation)
*   **Endpoint:** `GET /api/v1/graph/path/shortest/{lang}?from={qid}&to={qid}`
    - **Algorithm:** Cypher `shortestPath` (BFS).
*   **Endpoint:** `GET /api/v1/graph/path/simple/{lang}?from={qid}&to={qid}&limit=5`
    - **Algorithm:** `allShortestPaths` or limited depth traversals.

### 2.2 Local Neighborhood Scoring - [PARTIAL]
*   **Endpoint:** `GET /api/v1/graph/neighbors/scored/{lang}/{qid}`
*   **Implementation:** 
    - Cypher-based local metrics (Adamic-Adar, Jaccard).
    - Resolved against SQLite for titles in a single batch call.
*   **Metrics (Current):** `adamic_adar`, `jaccard`.

### 2.3 Global & Advanced Metrics - [PENDING]
*   **Pipeline:** `tools/analytics/compute_global_metrics.py` (Neo4j GDS -> Stream -> SQLite).
*   **Storage:** SQLite `node_metrics` table.
*   **Endpoint:** `GET /api/v1/graph/metrics/{lang}/{qid}`
*   **Algorithms:** PageRank, Betweenness, HITS.

---

## Phase 3: RAG & Context (The "AI Engineer")

**Goal:** Prepare high-quality context for LLMs (GraphRAG).

### 3.1 Context Retrieval Endpoint
*   **Endpoint:** `POST /api/v1/rag/context`
*   **Logic:**
    1.  **Retrieve:** Hybrid Search (FTS + Vector) to find anchor nodes.
    2.  **Expand:** Traverse Neo4j (1-hop) to find neighbors.
    3.  **Filter:** Use **HITS Authority** score (from SQLite) to keep only high-quality neighbors.
    4.  **Format:** Serialize Subgraph (Nodes + Metadata + Relations) to text.

---

## Phase 4: Live Data (The "Connector")

### 4.1 Wikimedia Bridge
*   **Endpoint:** `GET /api/v1/live/{lang}/{qid}`
*   **Implementation:** Async HTTP call to Wikipedia summary API. Non-blocking.