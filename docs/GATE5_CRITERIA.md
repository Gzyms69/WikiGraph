# Gate 5: Neo4j Import Validation Criteria

To declare Phase 4 complete, the Neo4j database must meet these strict metrics:

## 1. Data Integrity
- **Node Count:** 1,675,749 ± 1% (Range: 1,658,992 - 1,692,506)
- **Edge Count:** 99,903,827 ± 1% (Range: 98,904,788 - 100,902,866)
- **Schema:** 'Concept' label exists; 'LINKS_TO' relationship exists.
- **Constraints:** Uniqueness constraint on `Concept(qid)` is ONLINE.

## 2. Connectivity & Topology
- **Specific Path:** Q36 (Polska) -> Q270 (Warszawa) must exist (direct).
- **Source Verification:** 100 random edges sampled from `edges.csv` MUST exist in the graph.
- **Degree Distribution:** Max degree check. Warning if > 200,000.

## 3. Performance
- **Simple Query:** `MATCH (n:Concept {qid: 'Q36'}) RETURN n` < 100ms.
- **Path Query:** 3-hop expansion (`MATCH p=(n)-[*3]->(m) ... LIMIT 1`) < 2000ms.

