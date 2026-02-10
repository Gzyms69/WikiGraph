# API Expansion Plan: WikiGraph Master Plan

**Status:** Phase 1 (Search/Metadata) COMPLETED, Phase 2 (Core Graph) COMPLETED.
**Next:** Phase 1 Extension (Vectors) & Phase 3 (RAG).

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
*   **Safety:** GDS Memory Management Protocol enforced.

### 1.4 The "Rosetta Stone" Comparison - [DONE]
*   **Endpoint:** `GET /api/v1/compare/{qid}?langs=pl,de,es`
*   **Implementation:** Parallel `asyncio.gather` fetch.

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
*   **Algorithms (Computed - All Langs):** PageRank, HITS Authority, Louvain, Leiden, Triangle Count.

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
## Phase 1 Extension: The Visualizer (Frontend Integration)

**Goal:** Connect the verified Core Graph Engine to the Next.js Frontend.
*   **Integration:** Refactor the existing 3D-force-graph components to consume live API data from `/api/v1/entity`.
*   **UX Pattern:** Search Bar -> 3D Topology Visualization -> Sidebar Metadata Display.

## Phase 7: Hybrid AI Engine (Strategic Pivot)

**Goal:** Deliver generative "AI Insights" immediately using Cloud APIs, while architecting for future Local/Offline support.

### 7.1 AI Service Architecture (Provider Pattern)
*   **Design:** Implement a modular `AIService` with swappable backends.
*   **Interface:** `generate_insight(concept_id, related_nodes)`.
*   **Rationale:** Allows the system to demonstrate SOTA AI capabilities immediately while maintaining a path to full privacy/offline support.

### 7.2 Cloud Implementation (Gemini Flash)
*   **Provider:** `GeminiCloudProvider`.
*   **Technology:** `google-generativeai` (Google AI SDK).
*   **Feature:** Real-time summarization of entity relationships (e.g., "Summarize how Linux is related to Unix and Linus Torvalds").
*   **Endpoint:** `POST /api/v1/ai/insight`.

### 7.3 Offline Implementation (Future)
*   **Provider:** `LocalLlamaProvider`.
*   **Technology:** Ollama (Llama 3) + ChromaDB (Vector Store).
*   **Status:** Deferred to post-MVP phase.
