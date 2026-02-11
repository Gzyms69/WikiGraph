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

## Phase 8: Hybrid AI Engine (Strategic Pivot)

**Goal:** Deliver generative "AI Insights" immediately using Cloud APIs, while architecting for future Local/Offline support.

### 8.1 Cloud Implementation (Gemini Flash)
*   **Provider:** `GeminiCloudProvider`.
*   **Technology:** `google-generativeai` (Google AI SDK).
*   **Endpoint:** `POST /api/v1/ai/insight`.

---

# API Expansion Plan: WikiGraph Master Plan (MVP Sprint)

**Current Focus:** Delivering Hybrid AI Insights & Stability.
**De-prioritized:** Vector Search (moved to Phase 4).

## Phase 1 Extension: Live Data Bridge (The Safety Net) - [PRIORITY HIGH]
* **Endpoint:** Internal fallback within MetadataService.
* **Logic:** If local DB lacks abstract/infobox, fetch live from Wikipedia REST API (/summary/).
* **Value:** Prevents "empty card" scenarios during demo.

## Phase 3: Hybrid AI Engine (The "Intelligence Layer") - [ACTIVE]
**Goal:** Deliver generative insights immediately using Gemini 1.5 Flash.

### 3.1 AI Provider Architecture
* **Tech:** google-generativeai SDK (native).
* **Pattern:** Service-based (easy switch between Flash/Pro models).

### 3.2 Insight Endpoint
* **Endpoint:** POST /api/v1/ai/explain
* **Input:**
    { "lang": "pl", "subject_qid": "Q42", "context_nodes": ["Q1", "Q2"] }
* **Process:**
    1. Fetch Subject Title & Abstract (SQLite).
    2. Fetch Context Nodes Titles.
    3. Construct Prompt: "Explain the relationship between [Subject] and [Context Nodes] in 2 sentences."
    4. Return streaming or static response.
