# API Expansion Plan: WikiGraph Master Plan

**Status:** Phase 1 (Search/Metadata) COMPLETED, Phase 2 (Core Graph) COMPLETED, Phase 7 (Visualizer) COMPLETED, Phase 8 (AI Engine) COMPLETED.
**Next:** Phase 1.2 (Live Data Bridge) & Phase 3 (RAG Context).

---

## Phase 1: Foundations & Search (The "Retriever") - **COMPLETED**

**Goal:** Make the graph searchable via Keywords (FTS) and Concepts (Vectors).

### 1.1 Universal Search (SQLite FTS5) - [DONE]
*   **Endpoint:** `GET /api/v1/search/{lang}?q={query}`
*   **Implementation:** 
    - Uses SQLite **FTS5** virtual tables (`articles_fts`) for sub-millisecond prefix and keyword matching.
    - Query logic: `MATCH "{query}*"` (Prefix support).

### 1.2 Vector Search (ChromaDB) - [PENDING]
*   **Infrastructure:** Integrate `chromadb` (Persistent Client) in `data/chroma`.
*   **Model:** `all-MiniLM-L6-v2` (via `sentence-transformers`).
*   **Pipeline:** `tools/ai/embed_articles.py` -> Batch processes SQLite articles -> Stores vectors in ChromaDB.
*   **Endpoint:** `GET /api/v1/search/{lang}?q={query}&type=semantic`

### 1.3 Infrastructure & Hardening - [DONE]
*   **Pooling:** Implemented `SQLAlchemy.QueuePool` in `app/services/sqlite_pool.py`.
*   **Health:** `GET /api/v1/health` provides real-time status.
*   **CORS:** Added `CORSMiddleware` to `app/main.py` to allow frontend cross-origin requests.

### 1.4 The "Rosetta Stone" Comparison - [DONE]
*   **Endpoint:** `GET /api/v1/compare/{qid}?langs=pl,de,es`

---

## Phase 2: Core Graph Engine (The "Graph Mathematician") - **COMPLETED**

**Goal:** Provide deep structural insights using classical Graph Theory algorithms.

### 2.1 Navigation Engine (Pathfinding) - [DONE]
*   **Endpoint:** `GET /api/v1/graph/path/shortest/{lang}?from_qid={qid}&to_qid={qid}&max_depth=6`
*   **Implementation:** BFS with Progressive Timeout.

### 2.2 Local Neighborhood Scoring - [DONE]
*   **Endpoint:** `GET /api/v1/graph/neighbors/scored/{lang}/{qid}`
*   **Jaccard:** **[DONE]** Implemented via **Neo4j GDS** (`nodeSimilarity.filtered`). Performance < 3s.
*   **Resource Allocation:** **[DONE]** Implemented via Optimized Cypher (`LIMIT 2000`). Performance < 10s.
*   **Adamic Adar:** **[DONE]** Implemented via Optimized Cypher (`LIMIT 2000`).

### 2.3 Global & Advanced Metrics - [DONE]
*   **Endpoint:** `GET /api/v1/graph/metrics/{lang}/{qid}`
*   **Algorithms:** PageRank, HITS Authority, Louvain, Leiden, Triangle Count.

---

## Phase 3: RAG & Context (The "AI Engineer")

**Goal:** Prepare high-quality context for LLMs (GraphRAG).

### 3.1 Context Retrieval Endpoint
*   **Endpoint:** `POST /api/v1/rag/context`
*   **Logic:**
    1.  **Retrieve:** Hybrid Search (FTS + Vector) to find anchor nodes.
    2.  **Expand:** Traverse Neo4j (1-hop).
    3.  **Filter:** Use **HITS Authority** score.
    4.  **Format:** Serialize Subgraph.

---

## Phase 4: Live Data (The "Connector")

### 4.1 Wikimedia Bridge
*   **Endpoint:** `GET /api/v1/live/{lang}/{qid}`
*   **Implementation:** Async HTTP call to Wikipedia summary API.

---

## Phase 7: The Visualizer (Frontend Integration) - **COMPLETED**

**Goal:** Connect the verified Core Graph Engine to the Next.js Frontend.

### 7.1 Unified Bridge Endpoints - [DONE]
*   **Nebula Engine:** `GET /api/v1/graph/nebula/{lang}`. Fuses SQLite (PageRank) + Neo4j (Topology).
*   **Expansion Bridge:** `GET /api/v1/graph/weighted-neighbors/{lang}/{qid}`. Compatibility wrapper for expansion.
*   **Discovery Bridge:** `GET /api/v1/graph/languages`. Dynamic discovery of active containers.

### 7.2 Language-Agnostic Frontend - [DONE]
*   **Technology:** Next.js (App Router), `react-force-graph-3d`.
*   **Feature:** UI dynamically scales to available backend languages. No hardcoding.

---

## Phase 8: Graph‑Grounded AI Insights (COMPLETED – Feb 12, 2026)

**Strategic Pivot:** AI now narrates *analytical metrics*, not just titles.  
All insights are grounded in pre‑computed graph metrics (PageRank, HITS, communities, similarity scores).  

### 8.0 Node Card Real‑Metrics Upgrade - [DONE]
**Goal:** Replace misleading placeholders with accurate, meaningful metrics using existing API endpoints.

| Metric (API field) | Display Label | Status |
|-------------------|---------------|--------|
| `pagerank`        | Global Importance | [DONE] |
| `triangle_count`  | Local Clustering  | [DONE] |
| `auth_score`      | Authority (HITS)  | [DONE] |
| `louvain_id`      | Community (Coarse) | [DONE] |
| `leiden_id`       | Community (Fine)  | [DONE] |
| `degree`          | Degree (In+Out)   | [DONE] |

### 8.1 Analytical AI Endpoints (Backend) - [DONE]

**Endpoint – `POST /api/v1/ai/analyze/{lang}/{qid}`**  
*Implementation:* 
1. **Context Gathering:** Parallel fetch of metadata, analytical metrics, and top similar neighbors (Adamic-Adar + Jaccard).
2. **Dossier Compilation:** Translates raw metrics into a human-readable structural briefing.
3. **Grounded Prompting:** Instructs Gemini 2.5 Flash to act as a "Graph Intelligence Analyst" and synthesize math with metadata.
4. **Resilience:** Automatic fallback to Mock Insight on 429 quota errors.

### 8.2 Frontend AI Integration - [DONE]

- **AIInsightCard:** Collapsible card with interactive trigger ("Analyze with AI").
- **Session Caching:** Insights are cached in a global Map to prevent redundant API calls when navigating back to a node.
- **Dynamic Labeling:** Displays the exact model name (e.g., "Gemini 2.5 Flash") dynamically from the API response.
