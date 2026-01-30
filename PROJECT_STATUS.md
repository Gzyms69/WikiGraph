# WikiGraph: Project Status

## Recent Milestones (January 28, 2026)

### Gate 5B.5: Metadata Enrichment (COMPLETED)
- **Objective:** Extract structured data (infoboxes) from Wikipedia dumps into SQLite.
- **Polish Success:**
    - **Strategy:** Adopted "Germinator" strategy (Suffix Pattern Support).
    - **Yield:** 79% (1.3M records). Validated against suffix patterns (`X infobox`).
- **German Success:**
    - **Strategy:** Expanded config to include `Taxobox` and `Personendaten`.
    - **Yield:** 62% (1.9M records). Captured ~1M biographies and ~60k species.
- **Validation:** 
    - 100% JSON integrity on random samples.
    - Cross-language parity verified for major concepts.

### Gate 5B.3: Cross-Language Traversal (COMPLETED)
- **Algorithm:** Level-Synchronous BFS with per-node limit distribution.
- **Performance:** 1000-node traversal: ~2.1s.

## Current Data Inventory

| System | Language | Nodes/Pages | Edges/Rels | Properties |
| :--- | :--- | :--- | :--- | :--- |
| **Neo4j** | PL | 1.67M | 99.9M | qid, ns, title, out_degree, in_degree |
| **Neo4j** | DE | 3.10M | 149.4M | qid, ns, title, out_degree, in_degree |
| **SQLite**| PL | 2.60M | N/A | title, namespace, qid, **infobox (1.3M)** |
| **SQLite**| DE | 5.58M | N/A | title, namespace, qid, **infobox (1.9M)** |

## Known Issues
- **Import Pipeline Gap:** The `prepare_neo4j_csv.py` script needs to be permanently updated to include titles for future rebuilds. Currently relying on post-import enrichment.
- **Missing Edge Validation:** No source of truth for edges exists outside of Neo4j (pagelinks table missing in SQLite).

## Next Steps
- [ ] **Gate 5B.5.12:** API Restoration (Serve enriched metadata).
- [ ] **Gate 5B.5.13:** Pipeline Consolidation (Merge tools).
- [ ] Implement Community Detection (Louvain) to pre-calculate cluster IDs.
- [ ] Integration with Frontend WikiNebula visualization.