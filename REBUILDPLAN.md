# WikiGraph Rebuild Plan: Hybrid, Multi-Source Knowledge Graph Lab

## 🚧 Progress Tracker (Updated: 2026-01-17)
*   **Protocol:** Adopted "Fail-Safe" pipeline with strict validation gates.
*   **Previous Status:** **Phase 4A Complete (Multi-Language Infrastructure).**
    *   Neo4j containers isolated (`neo4j-pl`, `neo4j-de`).
    *   Polish Graph: 1.67M Nodes, 99.9M Edges.
    *   German Graph: 3.10M Nodes, 149.4M Edges.
*   **Current Status:** **Phase 5: Unified Backend API (In Progress).**
    *   Gate 5A.1 (Skeleton): Passed.
    *   Gate 5A.2 (Connection Manager): Passed.
    *   **Gate 5A.3 (Health Endpoint):** Pending Validation.

## 🛡️ Fail-Safe Implementation Protocol
**Core Principle:** "Make it work (correctly), then make it fast."
1.  **Gate 0 (Library Validated):** `mwsql` confirmed as viable parser.
2.  **Gate 1 (Row Count):** `pages` table must match official Wikipedia stats (~1.6M for PL) ±1%.
3.  **Gate 2 (Data Integrity):** Category names must be readable UTF-8, resolving `cl_target_id`.
4.  **Gate 3 (Clean CSVs):** Checksum verified before Graph DB import.
5.  **Gate 4 (Graph Verified):** Neo4j node/edge counts match CSVs; connectivity validated; uniqueness constraints active.
6.  **Gate 5 (Backend Integration):** API successfully routes queries to correct container and handles degradation.

## 1. Overview & Goals

**Primary Goal:** Build a versatile, research-grade knowledge graph system that serves two primary use cases:
1.  **The Offline Lab:** A full-featured, local installation built from Wikipedia dumps, offering researchers complete control, offline access, and deep metadata (categories, infoboxes).
2.  **The Online Showcase:** A public, deployable instance that uses the Wikidata Query Service (WDQS) to demonstrate global, cross-language graph capabilities with minimal setup overhead.

**Architecture Strategy:** **Virtual Bridge.** The Backend API acts as the federation layer, orchestrating queries across isolated language databases. This avoids the complexity of a physical bridge database while enabling linear scalability.

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

## 3. Data Source Strategy & Extraction

We now manage two parallel data flows.

| **Data Source** | **Core Idea** | **What It Provides** | **Our Usage & Integration** |
| :--- | :--- | :--- | :--- |
| **Direct SQL/XML Dumps** | Process raw database dumps line-by-line. | Complete article graph, full metadata (categories, infoboxes, summaries), and text for selected languages. | **Primary source for the Offline Lab.** Builds the localized Neo4j+SQLite+Text archive. Provides the deepest, most customizable analysis. |
| **Wikidata Query Service (WDQS)** | Query the live, global Wikidata graph via SPARQL. | Instant access to the global web of concepts (`wdt:P31`/instance of, `wdt:P279`/subclass of) and interlanguage links (`schema:about`). | **Primary source for the Online Showcase.** Powers the public demo with zero build time. **Augments the Offline Lab** by filling in missing interlanguage links or providing a baseline global structure. |

## 4. Detailed Data Pipeline & Storage Schema

### 4.1. Tier 1: The Graph Layer (Source-Agnostic)
*   **Purpose:** Execute graph algorithms and pathfinding.
*   **Schema:** Minimal and QID-based.
*   **Isolation:** Separate `neo4j-community` containers for each language to bypass Community Edition single-db limits and ensure full isolation.

### 4.2. Tier 2: SQLite Metadata Hub (Distributed)
*   **Purpose:** Central, fast access to all metadata.
*   **Schema:** Per-language databases (`pl.db`, `de.db`) are preferred during ingestion to allow parallel processing. The API connects to the specific DB based on the query context.

## 6. Phased Implementation Plan (Revised)

**Phase 4A: Multi-Language Infrastructure (Complete)**
*   [x] Create `config/infrastructure.yaml` to define ports and paths.
*   [x] Refactor `dev.sh` to support multi-container orchestration.
*   [x] **German Import:** Download, Ingest, Topology, Import.

**Phase 5: Unified Backend API (Current)**
*   [x] **Gate 5A.1:** Backend Skeleton & Config.
*   [x] **Gate 5A.2:** Connection Manager & Degradation.
*   [ ] **Gate 5A.3:** Health Endpoint.
*   [ ] **Gate 5A.INT:** Integration & Cross-Language Queries.

**Phase 6: Hybrid Features (Future)**
*   [ ] WDQS Integration.
*   [ ] Cross-language search.

## 7. Potential Roadblocks & Mitigations

| **Roadblock** | **Risk Level** | **Mitigation Strategy** |
| :--- | :--- | :--- |
| **Resource Contention** | High | Running multiple Neo4j instances requires RAM. **Mitigation:** Use strict Docker memory limits (4GB per container). Only start the language being actively queried if RAM is tight. |
| **German Umlauts** | Medium | Character encoding issues. **Mitigation:** Strict UTF-8 enforcement in `mwsql` and CSV generation. New "Gate 5" validation step. |

## 8. Success Metrics & Validation

*   **Metric:** Simultaneous query of Polish and German graphs via the API.
*   **Metric:** Zero data cross-contamination.

## Legacy Functionality Documentation (Generated by Cleanup Script)

### Backend Routers (Moved to `legacy/backend_old/routers/`)

#### analytics.py


**Endpoints:**
  - @router.post("/initialize")
  - @router.post("/pagerank")
  - @router.post("/bridges")
  - @router.post("/silos")
  - @router.post("/k-core")
  - @router.get("/gaps")

#### graph.py


**Endpoints:**
  - @router.get("/languages")
  - @router.post("/bulk-weighted-neighbors")
  - @router.get("/shortest-path")
  - @router.get("/nebula")
  - @router.post("/weighted-neighbors")
  - @router.get("/recommendations")

#### ml.py


**Endpoints:**
  - @router.post("/embeddings")

#### search.py


**Endpoints:**
  - @router.get("/keyword")


### Frontend Files (To be moved to `legacy/frontend_old/`)

- ./website/next.config.js
- ./website/postcss.config.js
- ./website/tailwind.config.js
- ./tests/e2e_site_check.js

## Production Frontend (`frontend/`)

### Overview
The production frontend is a Next.js (React) application with 3D graph visualization.

### Dependencies (Key)
- `3d-force-graph`: 3D force-directed graph rendering
- `react-force-graph-3d`: React wrapper for 3D force graph
- `axios`: HTTP client for API calls
- `three.js`: 3D graphics library
- `next`: React framework

### Architecture
```
frontend/
├── src/components/           # React components
│   └── nebula/              # Graph visualization components
│       └── InitializationScreen.tsx  # API integration example
├── package.json             # Dependencies listed above
├── next.config.ts           # Next.js configuration
└── tsconfig.json            # TypeScript configuration
```

### API Integration
- Uses `axios` for HTTP requests
- API base URL: `${API_BASE}/graph/languages` (from InitializationScreen.tsx)
- Expected to integrate with backend endpoints

### Current Status
- Codebase exists but integration with new backend (Gates 5B.1, 5B.2) may need updates
- 3D graph visualization components present
- Requires connection to updated API endpoints

### Rebuild Notes
1. Update API endpoints to match new backend routes (`/api/...`)
2. Test integration with language-specific endpoints
3. Verify 3D graph works with new data structures
4. Consider updating to use QID-based queries instead of title-based

## Static Documentation Site (`website/`) - MOVED TO LEGACY
**Location:** `legacy/frontend_old/website/`
**Purpose:** GitHub Pages static documentation and demo
**Technology:** Next.js static site
**Note:** This is separate from the production frontend and was used for documentation only.

## Legacy E2E Test
**Location:** `legacy/tests/e2e_site_check.js`
**Purpose:** End-to-end testing of the old frontend
**Status:** Requires updating for new frontend structure
