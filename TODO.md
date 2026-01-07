# WikiGraph Lab: Roadmap & TODO

## 🔍 Vision
Transform WikiGraph from a scalable backend engine into a full-stack **Research Platform** featuring a **3D Interlingual Nebula**—a high-performance visual universe of human knowledge.

---

## Phase 1: Infrastructure & Graph Science (Backend)
**Status:** COMPLETE ✅
- [x] **Neo4j GDS Integration** (APOC + GDS Plugins)
- [x] **FastAPI Service (`app/`)**
- [x] **Analytics Baseline** (Initialize, PageRank)
- [x] **Semantic Search** (Lucene Indexing)
- [x] **Research Features** (Bridges, Silos, Gaps)
- [x] **AI/ML & Personalized Relevance** (Embeddings, Recommendations)
- [x] **Scalability Hardening** (Optimized GDS projections, automated stress tests)

---

## Phase 2: The 3D Interlingual Nebula (Frontend)
**Status:** In Progress 🏗️
- [x] **Next.js 14 Setup** (Tailwind + TypeScript)
- [x] **3D Force Engine** (react-force-graph-3d)
- [x] **Universal Search & Fly-to** (Fix simulation-aware centering)
- [x] **Dynamic Node Expansion** (Fetch neighbors on click)
- [ ] **Refactor WikiNebula:** Split monolithic component into `NebulaControls`, `NodeDetailsPanel`, `SearchOverlay`.
- [ ] **Mission Control UI:**
    - [ ] **Details Deck:** Slide-out glassmorphism panel with metadata, metrics, and actions (Expand, Open Wiki).
    - [ ] **Control Deck:** Bottom bar for Physics (Play/Pause), Auto-Rotate, and Camera Reset.
- [ ] **Advanced Visuals:**
    - [ ] **Spotlight Mode:** Dim non-neighbors when a node is selected.
    - [ ] **Community Coloring:** Toggle node colors by Louvain Community ID.
- [ ] **Performance & UX:**
    - [ ] **Node Limiter Slider:** UI control for API fetch limits.
    - [ ] **Adaptive Labeling:** Only show labels on hover or for high-PageRank nodes.
- [ ] **Interlingual Wormholes:** Visual light-trails for Shortest Paths bridging languages.
- [ ] **"Time-Travel" Slider:** Visualize graph evolution (requires historical dump ingestion).

---

## Phase 3: Research Utilities & Scalability
- [ ] **English Wikipedia Load:** Scale to ~1B edges (requires 32GB+ RAM).
- [ ] **Docker Compose:** Containerize the entire stack for easy deployment.
- [ ] **Notebook SDK:** Create a Python client (`wikigraph-sdk`) for easy integration with Jupyter/Colab.
- [ ] **Academic Export API:**
    - [ ] **Gephi Streaming/Export:** Support `.gexf` or `.graphml` with computed metrics (PageRank, Community) as attributes.
    - [ ] **Citation Network Extraction:** Export references as a secondary graph layer.

---

## Phase 4: Advanced Academic Analysis (New) 🎓
*Inspirations from Connected Papers, Obsidian, and Network Science.*

- [ ] **Semantic Gap Detection (NLP + Graph):**
    - Use node embeddings (FastRP) + Text Embeddings (BERT/SentenceTransformers) to find articles that are *semantically* related but *structurally* unlinked ("Missing Link" recommendation).
- [ ] **Bias & Coverage Analyzer:**
    - Comparative topology metrics: "Is the 'Women Scientists' subgraph less densely connected than 'Men Scientists'?"
    - Cross-Lingual Disparity: Quantify information loss between EN and DE/PL graphs for the same topic.
- [ ] **Key Player Identification:**
    - **Betweenness Centrality:** Identify "Bridge Articles" that connect disparate fields (e.g., Mathematics <-> Biology).
    - **Structural Holes:** Identify users/topics that span disconnected communities.
- [ ] **Bibliometric Features:**
    - Ingest `cite_ref` tags to build a "Source Reliability" score for nodes based on external citation diversity.

---

## 💡 Technical Insights
*   **ID Synchronization:** Standardized on `lang:qid` across the stack to fix zoom/focus bugs.
*   **Simulation Stability:** Camera fly-to must wait for `onEngineTick` to ensure nodes have coordinates.
*   **Performance:** SAMPLING is required for Betweenness on 150M+ edges.
