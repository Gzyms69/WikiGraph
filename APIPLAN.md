# API Expansion Plan: WikiGraph Master Plan

**Status:** Phase 1 (Search/Metadata) COMPLETED, Phase 2 (Core Graph) COMPLETED, Phase 7 (Visualizer) COMPLETED.
**Next:** Phase 1.2 (Live Data Bridge) & Phase 3 (AI Engine).

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

## Phase 8: Graph‑Grounded AI Insights (Revised – Feb 12, 2026)

**Strategic Pivot:** AI now narrates *analytical metrics*, not just titles.  
All insights are grounded in pre‑computed graph metrics (PageRank, HITS, communities, similarity scores).  
**The previous `/api/v1/ai/insight` plan (titles‑only) is deprecated and superseded by the endpoints below.**

### 8.0 Frontend Foundation – Node Card Real‑Metrics Upgrade
**Goal:** Replace misleading placeholders with accurate, meaningful metrics using **existing API endpoints only**.  
**No new backend code.**

| Current UI Label | Actual Source | New Label | Action |
|------------------|---------------|-----------|--------|
| `Connectivity`   | PageRank (capped) | **Global Importance (PageRank)** | Remove cap, display raw PR or percentile. |
| `Cluster 0`      | Hardcoded placeholder | **Community (Louvain/Leiden)** | Fetch `louvain_id` from `/metrics/{lang}/{qid}`. |
| `val` (node size)| PageRank | **Importance** | Already correct – keep. |
| *(missing)*      | Triangle Count | **Local Clustering** | Add to panel. |
| *(missing)*      | Authority Score | **Authority (HITS)** | Add to panel. |
| *(missing)*      | Degree Centrality | **Degree** | Compute from neighbor count (available in `/entity`). |

**Implementation:**  
- Modify `NodeDetailsPanel.tsx` to call `/metrics/{lang}/{qid}` and render all available metrics.  
- Remove the fake `(node.val / 20) * 100` formula.  
- Add tooltips explaining each metric (on hover, showing definition, meaning, and calculation formula).

---

### 8.1 Analytical AI Endpoints (Backend)

**Endpoint A – `POST /api/v1/ai/analyze-node`**  
*Request:* `{ "lang": str, "qid": str }`  
*Context gathered:* title, abstract, PageRank, triangle count, authority, community ID, top‑5 similar nodes (Adamic‑Adar/Jaccard), community size & central nodes.  
*Prompt:* Grounded explanation of the node’s role in the graph.  

**Endpoint B – `POST /api/v1/ai/compare-nodes`**  
*Request:* `{ "lang": str, "qid1": str, "qid2": str }`  
*Context gathered:* both nodes’ metrics, their similarity score, community overlap, comparative statements.  
*Prompt:* Concise, metric‑driven comparison.  

**Provider Architecture (unchanged):**  
- Modular `AIService` with `GeminiFlashService` and `MockAIService`.  
- `google-generativeai` SDK, API key from `.env`.

---

### 8.2 Frontend AI Integration

- **NodeDetailsPanel:** Add “Analyze with AI” button → calls `analyze-node`, displays insight in collapsible card.  
- **Two‑node selection mode:** “Compare with another node” → calls `compare-nodes`.  
- Placeholder UI (skeleton loaders) implemented in Sprint 8.2.

**All AI features are OPT‑IN – no automatic API calls.**

**Expanded Metrics Display (Sprint 8.0 – Amendment):**  
The Node Card will display **all available node‑level metrics** from `/metrics/{lang}/{qid}`:

| Metric (API field) | Display Label | Notes |
|-------------------|---------------|-------|
| `pagerank`        | Global Importance | Raw PageRank value (unbounded, higher = more central). |
| `triangle_count`  | Local Clustering  | Number of triangles (higher = more tightly clustered neighborhood). |
| `auth_score`      | Authority (HITS)  | Authority score – cited by many hubs. |
| `louvain_id`      | Community (Coarse) | Louvain community ID. |
| `leiden_id`       | Community (Fine)  | Leiden community ID (higher resolution). |
| `degree` (from `/entity`) | Degree | Number of direct neighbors. |

All metrics include tooltips with definition, meaning, and interpretation.
