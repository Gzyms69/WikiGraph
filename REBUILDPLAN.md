# WikiGraph Rebuild Plan: Hybrid, Multi-Source Knowledge Graph Lab

## 🚧 Progress Tracker (Updated: 2026-01-15)
*   **Protocol:** Adopted "Fail-Safe" pipeline with strict validation gates.
*   **Tooling:** Selected `mwsql` library for robust SQL parsing (Gate 0 Passed).
*   **Current Status:** **Phase 4 Complete (Polish Graph Validated).**
    *   Neo4j graph built and verified: 1,675,749 nodes, 99,903,827 edges.
    *   Graph is live in `neo4j-pl` container.
*   **Next Step:** **Phase 4A (Multi-Language Infrastructure).**
    *   Implement multi-container architecture (one Neo4j instance per language).
    *   Execute full pipeline for German Wikipedia (`dewiki`).

## 🛡️ Fail-Safe Implementation Protocol
**Core Principle:** "Make it work (correctly), then make it fast."
1.  **Gate 0 (Library Validated):** `mwsql` confirmed as viable parser.
2.  **Gate 1 (Row Count):** `pages` table must match official Wikipedia stats (~1.6M for PL) ±1%.
3.  **Gate 2 (Data Integrity):** Category names must be readable UTF-8, resolving `cl_target_id`.
4.  **Gate 3 (Clean CSVs):** Checksum verified before Graph DB import.
5.  **Gate 4 (Graph Verified):** Neo4j node/edge counts match CSVs; connectivity validated; uniqueness constraints active.
6.  **Gate 5 (Multi-Language):** Character encoding and schema validation specific to the target language.

## 1. Overview & Goals

**Primary Goal:** Build a versatile, research-grade knowledge graph system that serves two primary use cases:
1.  **The Offline Lab:** A full-featured, local installation built from Wikipedia dumps, offering researchers complete control, offline access, and deep metadata (categories, infoboxes).
2.  **The Online Showcase:** A public, deployable instance that uses the Wikidata Query Service (WDQS) to demonstrate global, cross-language graph capabilities with minimal setup overhead.

**Architecture Strategy:** **Strict Isolation.** Each language lives in its own dedicated Neo4j container. This prevents encoding conflicts, schema collisions, and allows independent scaling. A unified API layer routes queries to the correct container.

## 2. Revised System Architecture (Multi-Container)

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

## 4. Detailed Data Pipeline & Storage Schema (Extended)

### 4.1. Tier 1: The Graph Layer (Source-Agnostic)
*   **Purpose:** Execute graph algorithms and pathfinding.
*   **Schema:** Minimal and QID-based.
*   **Isolation:** Separate `neo4j-community` containers for each language to bypass Community Edition single-db limits and ensure full isolation.

### 4.2. Tier 2: SQLite Metadata Hub (Distributed)
*   **Purpose:** Central, fast access to all metadata.
*   **Schema:** Per-language databases (`pl.db`, `de.db`) are preferred during ingestion to allow parallel processing. The API connects to the specific DB based on the query context.

## 6. Phased Implementation Plan (Revised)

**Phase 4A: Multi-Language Infrastructure (Current)**
*   [ ] Create `config/languages.yaml` to define ports and paths.
*   [ ] Refactor `dev.sh` to support multi-container orchestration.
*   [ ] **German Import:**
    *   Download `dewiki` dumps (Gate 4A-0: Checksums).
    *   Run SQLite ingestion (`de.db`).
    *   Generate CSVs (`data/neo4j_bulk/de/`).
    *   Import into `neo4j-de` container.
*   *Ease: Medium. Confidence: High.*

**Phase 5: Unified Backend API (Week 5)**
*   [ ] Update backend to read `languages.yaml`.
*   [ ] Implement `GraphService` factory to select the correct driver (`bolt://localhost:7687` vs `7688`).
*   [ ] Verify API connectivity to both graphs.

**Phase 6: Hybrid Features (Week 6)**
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