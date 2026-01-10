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

## Phase 3.5: True Language Agnosticism (The Universal Engine)
**Status:** IN PROGRESS 🚧
*Goal: Remove all linguistic hardcoding to support any of the 300+ Wikipedia languages automatically.*

### ✅ Implemented
- [x] **Dynamic Configuration (JIT):** Auto-fetch namespace/redirect rules from MediaWiki API (`fetch_lang_config.py`).
- [x] **Codebase De-biasing:** Removed all `lang='pl'` defaults from function signatures.
- [x] **Frontend Adaptability:** Dynamic language toggles and localized display names (`Intl.DisplayNames`).
- [x] **Universal Tokenization:** Implemented character-level tokenization for CJK (Chinese, Japanese, Korean) languages.

### 🚧 Critical Gaps (To Be Implemented)
- [ ] **Standardized Property Ingestion:**
    - Parse `page_props` dumps to extract `disambiguation`, `hiddencat` flags.
    - This allows filtering "garbage" nodes without hardcoded template names.
- [ ] **Main Page Identification:**
    - Fetch `siteinfo.general.mainpage` via JIT and blacklist it to prevent artificial hubs.
- [ ] **Unicode Normalization (NFC):**
    - Enforce `unicodedata.normalize('NFC', title)` on all text to fix "café" mismatches (Mac vs Linux encoding issues).
- [ ] **Robust Case Folding:**
    - Replace `.lower()` with `.casefold()` to handle Turkish `I/İ` and other complex case mappings.
- [ ] **Regex Universality:**
    - Audit all regexes to ensure `\w` matches Unicode characters (Python 3 does this by default, but verification is needed for specific ranges).

---

## 🔥 Known Issues & Debug Log (Pending Deployment)
*These errors were identified during the Agnostic Stress Test. Fixes are in code but need server restart/verification.*

- [ ] **Shortest Path Self-Loop (gql_status: 51N23):**
    - **Issue:** Neo4j `shortestPath` fails if `start == end`.
    - **Fix:** (Applied) Check `if start == end` in API and return 0-hop path immediately.
- [ ] **GDS License Concurrency Violation:**
    - **Issue:** `betweenness` failed with `concurrency: 8` on free license.
    - **Fix:** (Applied) Limit to `concurrency: 4` in `analytics.py`.
- [ ] **FastRP Memory Overload (java.lang.IllegalStateException):**
    - **Issue:** Running `fastRP` with 32-dim on large graph exceeds 3GB heap.
    - **Fix:** (Planned) Update `api_stress_test.py` to use `dimensions=4` for smoke testing. Use `gds.graph.project` with node filtering to reduce graph size if needed.

---

## Phase 3: Research Utilities & Scalability (Next Steps)
**Status:** Planned 📋
- [ ] **English Wikipedia Load:** Scale to ~1B edges.
- [ ] **Docker Compose:** Containerize the stack.
- [ ] **Notebook SDK:** Create `wikigraph-sdk` Python client.
- [ ] **Adaptive Labeling:** Reduce 3D clutter.
