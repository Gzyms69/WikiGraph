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
**Status:** COMPLETE ✅
- [x] **Next.js 14 Setup** (Tailwind + TypeScript)
- [x] **3D Force Engine** (react-force-graph-3d)
- [x] **Universal Search & Fly-to** (Fix simulation-aware centering)
- [x] **Dynamic Node Expansion** (Fetch neighbors on click)
- [x] **Refactor WikiNebula:** Split monolithic component into `ControlDeck`, `NodeDetailsPanel`, `SearchOverlay`.
- [x] **Mission Control UI:**
    - [x] **Details Deck:** Slide-out glassmorphism panel with metadata.
    - [x] **Control Deck:** Bottom bar for Physics, Auto-Rotate, and Camera Reset.
- [x] **Advanced Visuals:**
    - [x] **Spotlight Mode:** Dim non-neighbors when a node is selected.
    - [x] **Community Coloring:** Toggle node colors by Louvain Community ID.
- [x] **Performance & UX:**
    - [x] **Near-Instant Initial Load:** Precompute high-PageRank "seed nodes".
    - [x] **Optimized Search & Spawn:** Accelerate search for "unmapped" nodes.
    - [x] **Node Summoning UI:** Visual feedback during API calls.

---

## Phase 2.5: Hybrid Intelligence & Interaction
**Status:** COMPLETE ✅
- [x] **Weighted Multi-Algorithm Ranking:**
    - Backend: Jaccard (Synonyms), Adamic-Adar (Context), and PageRank (Influence) blending.
    - Normalization: Min-Max scaling to mix 0-1 scores with unbounded log scores.
- [x] **System Settings Panel:**
    - Multi-select algorithms.
    - Real-time weight sliders.
    - Physics tuning (Gravity, Link Distance).
- [x] **Bulk Graph Operations:**
    - **Regenerate Knowledge:** Batch-refresh all visible nodes with new algorithm settings.
    - **Stability Merge:** Preserve node positions (`x, y, z`) during refreshes to prevent layout jumps.

---

## Phase 3: Research Utilities & Scalability (Next Steps)
**Status:** Planned 📋
- [ ] **English Wikipedia Load:** Scale to ~1B edges (requires 32GB+ RAM).
- [ ] **Docker Compose:** Containerize the entire stack for easy deployment.
- [ ] **Notebook SDK:** Create a Python client (`wikigraph-sdk`) for easy integration with Jupyter/Colab.
- [ ] **Academic Export API:**
    - [ ] **Gephi Streaming/Export:** Support `.gexf` or `.graphml`.
    - [ ] **Citation Network Extraction:** Export references as a secondary graph layer.
- [ ] **Adaptive Labeling:** Only show labels on hover or for high-PageRank nodes to reduce clutter.
- [ ] **"Time-Travel" Slider:** Visualize graph evolution (requires historical dump ingestion).

---

## Phase 4: Advanced Academic Analysis 🎓
*Inspirations from Connected Papers, Obsidian, and Network Science.*

- [ ] **Semantic Gap Detection (NLP + Graph):**
    - Use node embeddings (FastRP) + Text Embeddings (BERT) to find articles that are *semantically* related but *structurally* unlinked.
- [ ] **Bias & Coverage Analyzer:**
    - Comparative topology metrics: "Is the 'Women Scientists' subgraph less densely connected than 'Men Scientists'?"
    - Cross-Lingual Disparity: Quantify information loss between EN and DE/PL graphs.
- [ ] **Key Player Identification:**
    - **Betweenness Centrality:** Identify "Bridge Articles" that connect disparate fields.
    - **Structural Holes:** Identify users/topics that span disconnected communities.

---

## 💡 Technical Insights
*   **ID Synchronization:** Standardized on `lang:qid` across the stack to fix zoom/focus bugs.
*   **Simulation Stability:** Camera fly-to must wait for `onEngineTick` to ensure nodes have coordinates.
*   **Hybrid Ranking:** Adamic-Adar is the most effective default for finding "interesting" connections, while Jaccard is better for strict synonymy.
