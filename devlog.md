# Developer Log - WikiGraph Rebuild

## 2026-01-13: Emergency Protocol Activation (Connectivity Failure)

**Incident Report:**
*   **Event:** Failed Phase 2 (Topology) execution.
*   **Failure:** Ignored critical data quality warning. `edges.csv` contained only 77,706 edges for 1.95M nodes (0.03% connectivity).
*   **Protocol Violation:** Proceeded to import unvalidated data into Neo4j despite the obvious low link count. Modified `dev.sh` to fix startup issues without verifying the underlying config.
*   **Impact:** Neo4j database is currently populated with a disconnected, useless graph.

**Root Cause Analysis (COMPLETED):**
*   **Root Cause:** **Critical Schema Mismatch.**
    *   The `pagelinks` parser in `prepare_neo4j_csv.py` assumed the legacy MediaWiki schema: `(pl_from, pl_namespace, pl_title)`.
    *   The actual data uses the modern schema (MW 1.39+): `(pl_from, pl_from_namespace, pl_target_id)`.
    *   The code was interpreting `pl_target_id` (an integer) as the target *Title*.
    *   Result: Lookups for titles like "1", "2", "3" failed, resulting in 99.9% data loss.
*   **Contributing Factor:** The `link_targets` table in SQLite (`pl.db`) was populated but **missing the `lt_namespace` column**, rendering it insufficient for accurate link resolution even if we had used it.

**Recovery Plan:**
1.  **Fix Data Ingestion:**
    *   Modify `core/sqlite_loader.py` to include `lt_namespace` in the `link_targets` table.
    *   Drop and recreate `link_targets` table.
    *   Re-run ingestion for `plwiki-latest-linktarget.sql.gz`.
2.  **Fix Graph Generation:**
    *   Modify `core/tools/prepare_neo4j_csv.py` to:
        *   Load `link_targets` (ID -> Namespace, Title) from SQLite.
        *   Parse `pagelinks` using the correct schema (`pl_target_id`).
        *   Resolve links via the `link_targets` map.
3.  **Verification:**
    *   Run a diagnostic sample on 1% of links before full processing.

**Infrastructure Changes (To Be Reverted/Verified):**
*   Modified `dev.sh` to remove `NEO4J_server_gds_memory_limit`. This needs validation once the database is fixed.

## 2026-01-13: Recovery Phase 1 (Schema Fix)

**Action:**
*   Wiped broken Neo4j database and invalid CSVs.
*   Updating `core/sqlite_loader.py` to support `linktarget` schema correctly (adding `lt_namespace`).
*   Verification Gate 1: Test ingestion on 1000 rows.

### [2026-01-13 14:30] Gate 3 Diagnostic Passed
- **Test:** Full linear scan of `pagelinks` dump (sampled 1/10000).
- **Result:** 
  - 86.5% raw success rate.
  - 88.4% adjusted success rate (Article -> Article).
  - 0.0% missing targets in SQLite.
- **Root Cause Confirmed:** The `pagelinks` dump is sorted by `target_id`. Linear sampling from the head only saw Template links. Randomized sampling confirmed the graph is healthy.
- **Action:** Proceeding to Phase 3 (CSV Generation) with strict 1M row test limit first.


### [2026-01-13 14:35] Gate 4 Pre-check (1M Rows) Passed
- **Command:** `python3 core/tools/prepare_neo4j_csv.py --limit 1000000`
- **Results:**
  - Edges Created: 730,096 (73.0%)
  - Skipped (Namespace Filter): 261,604 (26.1%)
  - Unresolved (Redlinks): 616 (0.06%)
- **Conclusion:** Script logic is verified. Namespace filtering is active. Memory is stable.
- **Action:** Ready for full 214M row execution.


### [2026-01-13 14:30] Gate 3 Diagnostic Passed
- **Test:** Full linear scan of `pagelinks` dump (sampled 1/10000).
- **Result:** 
  - 86.5% raw success rate.
  - 88.4% adjusted success rate (Article -> Article).
  - 0.0% missing targets in SQLite.
- **Root Cause Confirmed:** The `pagelinks` dump is sorted by `target_id`. Linear sampling from the head only saw Template links. Randomized sampling confirmed the graph is healthy.
- **Action:** Proceeding to Phase 3 (CSV Generation) with strict 1M row test limit first.


### [2026-01-13 14:35] Gate 4 Pre-check (1M Rows) Passed
- **Command:** `python3 core/tools/prepare_neo4j_csv.py --limit 1000000`
- **Results:**
  - Edges Created: 730,096 (73.0%)
  - Skipped (Namespace Filter): 261,604 (26.1%)
  - Unresolved (Redlinks): 616 (0.06%)
- **Conclusion:** Script logic is verified. Namespace filtering is active. Memory is stable.
- **Action:** Ready for full 214M row execution.


### [2026-01-14] Phase 3: Full CSV Generation Started
- **Safety Test (1M rows):** Passed (730,096 edges, 261,604 skipped).
- **Status:** Proceeding with full 214M row processing.


### [2026-01-14] Phase 3 Complete
- **Final Nodes:** 1,675,749
- **Final Edges:** 99,903,827
- **Validation:** Gate 4 Passed using tools/verify_neo4j_csvs.py.
- **Next Step:** Proceed to Neo4j Admin Import.


### [2026-01-14] Phase 4: Readiness Check Passed
- **Disk:** 575GB free (PASSED)
- **Memory:** 23GB available, 12G Heap configured (PASSED)
- **Status:** Creating verification script before execution.


### [2026-01-14] Phase 4 Complete
- **Status:** Neo4j Import Successful.
- **Validation:** Gate 5 Passed (100% integrity, <30ms latency).
- **Configuration:** 4GB Heap / 4GB Pagecache (Safe Mode).
- **Constraints:** Uniqueness on `Concept(qid)` created.


### [2026-01-17] Phase 4A Complete (German Import)
- **German Graph:** Imported & Verified (149M edges).
- **Infrastructure:** Refactored `dev.sh` for multi-container support.
- **Validation:** Both PL and DE graphs passed Gate 5.

