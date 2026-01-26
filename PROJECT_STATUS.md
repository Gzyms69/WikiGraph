# WikiGraph: Project Status

## Recent Milestones (January 22, 2026)

### Gate 5B.3: Cross-Language Traversal (COMPLETED)
- **Algorithm:** Level-Synchronous BFS with per-node limit distribution (Fixing global starvation bug).
- **Hard Limits:** Max Depth: 3, Limit per Depth: 200, Total Nodes: 1000.
- **Safety:** Memory monitoring (1GB threshold) and 3s per-query timeouts implemented.
- **Data Enrichment:** 
    - Enriched 4.7M Neo4j nodes with `title` property from SQLite.
    - Pre-computed `out_degree` and `in_degree` for all nodes in Neo4j.
- **Performance:** 
    - 1000-node traversal: ~2.1s.
    - 200-node traversal: ~0.18s.
    - Throughput: ~3000-6000 edges/sec.

### Gate 5B.3.7: Import Pipeline Analysis (COMPLETED)
- **Status:** Validated CSV generation logic.
- **Findings:** Original import scripts failed to include `title` in CSVs.
- **Remediation:** Verified that patching scripts (`enrich_neo4j_titles.py`) successfully corrected the live database (100% title coverage achieved).

## Current Data Inventory

| System | Language | Nodes/Pages | Edges/Rels | Properties |
| :--- | :--- | :--- | :--- | :--- |
| **Neo4j** | PL | 1.67M | 99.9M | qid, ns, title, out_degree, in_degree |
| **Neo4j** | DE | 3.10M | 149.4M | qid, ns, title, out_degree, in_degree |
| **SQLite**| PL | 2.60M | N/A | title, namespace, qid |
| **SQLite**| DE | 5.58M | N/A | title, namespace, qid |

## Known Issues
- **Import Pipeline Gap:** The `prepare_neo4j_csv.py` script needs to be permanently updated to include titles for future rebuilds. Currently relying on post-import enrichment.
- **Missing Edge Validation:** No source of truth for edges exists outside of Neo4j (pagelinks table missing in SQLite).

## Updated: 2026-01-27
### Polish Infobox Complexity (New Understanding)
Polish Wikipedia uses two distinct infobox naming conventions:
1. **Modular templates (prefix):** `Infobox nagłówek`, `Infobox wiersz` - Used for structured articles
2. **Topic templates (suffix):** `* infobox` - Used for technical/content articles (e.g., "Język programowania infobox")

**Current limitation:** `pl.yaml` only configures for prefix patterns. Suffix patterns require:
- Configuration update (`template_suffixes` field)
- OR extraction logic update (contains/ends_with detection)
- OR both prefix and suffix detection

**Resolution strategy:** Deferred to Phase 3 (Polish Infobox Solution)

## Next Steps
- [ ] Implement Community Detection (Louvain) to pre-calculate cluster IDs.
- [ ] Add PageRank scores to Neo4j properties for better search ranking.
- [ ] Integration with Frontend WikiNebula visualization.