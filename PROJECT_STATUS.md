# WikiGraph: Project Status

## Recent Milestones (February 7, 2026)

### Phase 1: Foundations & Search (COMPLETED)
- **Search:** Implemented FTS5 keyword search for PL, DE, ES.
- **Comparison:** Implemented parallel cross-language metadata fetching.
- **Graph:** Implemented Adamic-Adar neighbor scoring in Neo4j with SQLite title resolution.
- **Hardening:** 
    - Full connection pooling (SQLAlchemy).
    - Health endpoint `/api/v1/health`.
    - Regex QID validation.
    - Graceful error handling for FTS syntax.

### Metadata Enrichment (COMPLETED)
- **Objective:** Extract structured data (infoboxes) from Wikipedia dumps into SQLite.
- **Yields:** 79% for Polish (Suffix), 62% for German (Multi-pattern).
- **Languages:** PL, DE, ES (JIT validated).

## Current Data Inventory

| System | Language | Nodes/Pages | Edges/Rels | Structured Data | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Neo4j** | PL | 1.67M | 99.9M | Topology | **ACTIVE** |
| **Neo4j** | DE | 3.10M | 149.4M | Topology | **ACTIVE** |
| **Neo4j** | ES | 2.02M | 64.7M | Topology | **ACTIVE** |
| **SQLite**| PL | 2.60M | N/A | FTS5 + 1.3M Infoboxes | **ACTIVE** |
| **SQLite**| DE | 5.58M | N/A | FTS5 + 1.9M Infoboxes | **ACTIVE** |
| **SQLite**| ES | 3.4M | N/A | FTS5 + 1.47M Infoboxes | **ACTIVE** |

## Next Steps
- [ ] **Phase 2: Core Graph Engine**
    - Implement Shortest Path (BFS) router.
    - Configure Neo4j GDS for PageRank/Betweenness streaming.
- [ ] **Phase 1 (Extension): AI Search**
    - Implement ChromaDB Vector Search.
- [ ] Integration with Frontend WikiNebula visualization.
