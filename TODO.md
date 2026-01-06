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
- [ ] **Interlingual Wormholes:** Visual light-trails for Shortest Paths bridging languages.
- [ ] **Galaxy Clustering UI:** Toggle visualization of Louvain Communities.

---

## Phase 3: Research Utilities & Scalability
- [ ] **English Wikipedia Load:** Scale to ~1B edges (requires 32GB+ RAM).
- [ ] **Subgraph Export API:** (GraphML/GEXF for Gephi).
- [ ] **Docker Compose:** Containerize the entire stack for easy deployment.

---

## 💡 Technical Insights
*   **ID Synchronization:** Standardized on `lang:qid` across the stack to fix zoom/focus bugs.
*   **Simulation Stability:** Camera fly-to must wait for `onEngineTick` to ensure nodes have coordinates.
*   **Performance:** SAMPLING is required for Betweenness on 150M+ edges.