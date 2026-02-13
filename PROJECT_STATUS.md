# WikiGraph: Project Status

## Recent Milestones (February 12, 2026)

### Phase 8: Hybrid AI Engine (ACTIVE - Sprint 8.2 COMPLETE)

- **AI Structural Intelligence:**
    - **Endpoint:** `POST /api/v1/ai/analyze/{lang}/{qid}`.
    - **Intelligence:** Implemented "Grounded Dossier" prompt engineering. The AI now receives PageRank, HITS, Clustering, Communities, and Contextual Similarities (Adamic-Adar/Jaccard) to explain a node's network significance.
    - **Resilience:** Implemented automatic fallback to "Structural Mock" summaries on 429 (Quota) errors or missing dependencies.
- **Node Card Real-Metrics Upgrade:**
    - **UI:** Completely overhauled `NodeDetailsPanel`. Replaced placeholders with real PageRank, Authority, Clustering, and Degree data.
    - **Context:** Added semantic tooltips for every mathematical metric.
    - **Persistence:** Implemented session-based caching for AI insights to save API costs and speed up navigation.

### Phase 7: The Visualizer (COMPLETED & INTEGRATED)

- **API Bridge:** 
    - `GET /api/v1/graph/nebula/{lang}`: Dynamic global view from SQLite (PageRank) + Neo4j (Links).
    - `GET /api/v1/graph/weighted-neighbors/{lang}/{qid}`: Universal similarity expansion bridge.
    - `GET /api/v1/graph/languages`: Dynamic discovery of active containers/configs.
- **Frontend Integration:**
    - **Language Agnostic:** No hardcoded languages; UI adapts to discovered backend containers.
    - **3D Engine:** High-performance visualization via `react-force-graph-3d`.
    - **Direct Wire-up:** Zero technical debt; frontend maps directly to FastAPI bridge.
- **Performance:** Initial nebula load < 200ms; neighbor expansion < 1s (Adamic-Adar).

### Phase 2: Core Graph Engine (COMPLETED & VERIFIED)

- **Pathfinding:** Configurable BFS (Depth 24) with progressive timeouts.
- **Global Metrics (Analytics):**
    - **Polish (PL):** PageRank, HITS, Louvain, Leiden, Triangle Count.
    - **Spanish (ES):** PageRank, HITS, Louvain, Leiden, Triangle Count.
    - **German (DE):** PageRank, HITS, Louvain, Leiden, Triangle Count.
- **Local Similarity (Scoring):**
    - **Jaccard:** **GDS-Accelerated** (`gds.nodeSimilarity`). Performance: <3s.
    - **Resource Allocation / Adamic Adar:** **Optimized Cypher** (`LIMIT 2000` safety valve). Performance: <10s.
- **Validation:** **Master Validation Suite (Gate 6)** passed for PL, DE, ES.

### Phase 1: Foundations & Search (HARDENED)

- **Search:** Universal FTS5 Search verified.
- **Metadata:** Rich Infobox retrieval verified across 3 languages.
- **Robustness:** Memory leaks addressed. Strict GDS cleanup protocol enforced.

## Current Data Inventory

| System | Language | Nodes/Pages | Edges/Rels | Structured Data | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Neo4j** | PL | 1.67M | 99.9M | Topology + Metrics (Full) | **VERIFIED** |
| **Neo4j** | DE | 3.10M | 149.4M | Topology + Metrics (Full) | **VERIFIED** |
| **Neo4j** | ES | 2.02M | 64.7M | Topology + Metrics (Full) | **VERIFIED** |
| **SQLite**| PL | 2.60M | N/A | FTS5 + 1.3M Infoboxes | **ACTIVE** |
| **SQLite**| DE | 5.58M | N/A | FTS5 + 1.9M Infoboxes | **ACTIVE** |
| **SQLite**| ES | 3.4M | N/A | FTS5 + 1.47M Infoboxes | **ACTIVE** |

## Roadmap

### Next Up: Phase 1 Extension (AI Search)
- [ ] Implement ChromaDB Vector Store.
- [ ] Create Embedding Pipeline (`tools/ai/embed_articles.py`).
- [ ] Implement Semantic Search Endpoint.

### Future: Phase 3 (RAG)
- [ ] Context Retrieval Endpoint.
- [ ] LLM Integration.