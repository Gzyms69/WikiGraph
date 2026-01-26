# WikiGraph Rebuild Plan: Hybrid, Multi-Source Knowledge Graph Lab

##  Progress Tracker (Updated: 2026-01-19)
*   **Protocol:** Adopted "Fail-Safe" pipeline with strict validation gates.
*   **Previous Status:** **Phase 4A Complete (Multi-Language Infrastructure).**
*   **Current Status:** **Cleanup Reorganization COMPLETED.**
    *   Legacy code archived in `legacy/`.
    *   Backend routing fixed.
    *   Ready for Gate 5B.3.

## 1. Comprehensive Legacy Feature Audit (The "Gold Standard")

We must eventually restore these features from the legacy codebase (`legacy/backend_old/routers/`).

### 1.1. Graph Topology & Traversal (`graph.py`)
*   **Weighted Neighbors (`/weighted-neighbors`):**
    *   **Logic:** Calculates neighbor relevance using a weighted sum of **Jaccard Coefficient**, **Adamic-Adar Index**, and **Personalized PageRank**.
    *   **Normalization:** Min-Max normalization of scores within the candidate set.
    *   **Filtering:** Excluded "List of", "Category:", etc.
*   **Shortest Path (`/shortest-path`):**
    *   **Logic:** Standard Neo4j `shortestPath` (BFS).
    *   **Feature:** Handled Start==End edge case.
*   **Nebula Sample (`/nebula`):**
    *   **Logic:** Fetched top PageRank nodes per language to create a "Universe" visualization.
    *   **Feature:** Balanced sampling (e.g., 50 PL, 50 DE).
*   **Languages (`/languages`):** Listed available datasets.

### 1.2. Network Analytics (`analytics.py`)
These features used the Neo4j Graph Data Science (GDS) library.
*   **PageRank (`/pagerank`):** Global influence scoring.
*   **Bridges (`/bridges`):** Used **Betweenness Centrality** to find nodes connecting clusters.
*   **Silos (`/silos`):** Used **Louvain Modularity** to find isolated communities.
*   **K-Core (`/k-core`):** Decomposed graph shells to find the dense core.
*   **Cross-Lingual Gaps (`/gaps`):** Found high-degree nodes in Lang A missing in Lang B.

### 1.3. Search & ML
*   **Keyword Search (`/search/keyword`):** Full-text Lucene index on `Article.title`.
*   **Embeddings (`/ml/embeddings`):** FastRP (Random Projection) node embeddings (16-dim).

### 1.4. Frontend Features (`frontend/`)
*   **Visual Engine:** `3d-force-graph` (Three.js) rendering.
*   **Control Deck:** Search, Language Toggle, Algorithm Weight Sliders (Jaccard/AA/PPR).
*   **Node Details:** Slide-out panel with abstract and metadata.

---

## 2. Revised System Architecture (Virtual Bridge)

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Frontend (Next.js)                         │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ HTTP/JSON
┌───────────────────────────────▼─────────────────────────────────────┐
│                     FastAPI Backend Service (Unified API)           │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                     Graph Query Engine                       │   │
│  │  ┌─────────────┐                            ┌─────────────┐  │   │
│  │  │  Lang Router│───────────────────────────►│   WDQS      │  │   │
│  │  └──────┬──────┘                            │   Adapter   │  │   │
│  └─────────┼───────────────────────────────────└─────────────┘  │   │
│            │                                                    │   │
│   ┌────────▼────────┐    ┌─────────────────┐                    │   │
│   │  Neo4j (PL)     │    │   Neo4j (DE)    │                    │   │
│   │ Port: 7474/7687 │    │ Port: 7475/7688 │                    │   │
│   └────────┬────────┘    └────────┬────────┘                    │   │
└────────────┼──────────────────────┼─────────────────────────────┘   │
             │                      │                                 │
        ┌────▼────┐            ┌────▼────┐                            │
        │  SQLite │            │  SQLite │                            │
        │  pl.db  │            │  de.db  │                            │
        └─────────┘            └─────────┘                            │
```

## 3. Phased Implementation Plan (Revised)

**Phase 4A: Multi-Language Infrastructure (Complete)**
*   [x] Create `config/infrastructure.yaml`.
*   [x] Refactor `dev.sh`.
*   [x] **German Import:** Download, Ingest, Topology, Import.

**Phase 5: Unified Backend API (Current)**
*   [x] **Gate 5A.1:** Backend Skeleton & Config.
*   [x] **Gate 5A.2:** Connection Manager & Degradation.
*   [x] **Gate 5A.3:** Health Endpoint.
*   [x] **Gate 5B.1:** QID Endpoints (Merged).
*   [x] **Gate 5B.2:** Language Endpoints (Pathfinding).
*   [ ] **Gate 5B.3:** Cross-Language Traversal (BFS).

### Phase 3: Polish Infobox Solution (Enhanced Scope)

#### Gate 5B.5.6: Polish Infobox Pattern Analysis (Enhanced)
**New understanding:** Two distinct patterns exist (prefix and suffix)

**Analysis tasks:**
1. **Pattern distribution analysis:**
   - Sample 100,000 Polish articles
   - Categorize by pattern: prefix, suffix, both, none
   - Calculate percentages and article types

2. **Configuration strategy:**
   - Option A: Add `template_suffixes: ['infobox']` to `pl.yaml`
   - Option B: Change detection logic to "contains 'infobox'"
   - Option C: Hybrid approach (both prefix and suffix lists)

3. **Parameter mapping validation:**
   - Verify parameter mappings work for both pattern types
   - Check for template name variations

#### Gate 5B.5.7: Polish Infobox Extraction (Updated)
**Implementation requirements:**
- Support both prefix and suffix detection
- Handle potential template name conflicts
- Apply parameter mapping correctly
- Store as JSON array with pattern type metadata

**Phase 6: Search & Advanced Features (The "Legacy Restoration")**
*   [ ] **Gate 6.1:** Keyword Search (Re-implement Lucene/Text index).
*   [ ] **Gate 6.2:** Weighted Neighbors (Port Jaccard/AA logic to new Multi-DB structure).
*   [ ] **Gate 6.3:** Analytics (Port GDS calls - requires GDS installation in containers).

## 4. Potential Roadblocks & Mitigations

| **Roadblock** | **Risk Level** | **Mitigation Strategy** |
| :--- | :--- | :--- |
| **GDS Compatibility** | High | GDS on multiple databases requires Enterprise or careful orchestration. **Strategy:** Run GDS on one language at a time or aggregate data in memory. |
| **Search Performance** | Medium | Lucene across 2 DBs + SQLite? **Strategy:** Use SQLite FTS5 for title search (fast, low overhead). |

## 5. Success Metrics

*   **Metric:** Simultaneous query of Polish and German graphs via the API.
*   **Metric:** Zero data cross-contamination.

## 6. Architectural Principle: Minimal Neo4j (Gate 5B.3.9)

**Decision (Jan 2026):** Neo4j must remain lean to maximize graph traversal performance and minimize memory footprint. Metadata should reside in SQLite.

*   **Neo4j:** Stores ONLY graph topology (Nodes `QID` and Relationships `LINKS_TO`).
*   **SQLite:** Stores ALL node attributes (`title`, `out_degree`, `in_degree`, `infobox`, `text`).
*   **Migration Plan:**
    1.  **Schema Update:** Add `out_degree` and `in_degree` columns to SQLite `pages` table.
    2.  **Cleanup:** Remove `title` and degree properties from Neo4j nodes.
    3.  **API Update:** Refactor Backend to fetch metadata from SQLite using QIDs returned by Neo4j.