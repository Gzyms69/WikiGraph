# WikiGraph Tasks

## 🛡️ Fail-Safe Pipeline (Current Priority)
### Phase 1: Metadata Extraction (Metadata)
- [x] **Gate 0:** Validate `mwsql` library capabilities (Passed).
- [ ] **Implementation:** Refactor `core/sqlite_loader.py` to use `mwsql` and support per-language DBs.
- [ ] **Execution:** Run import for Polish (`pl`) into `data/db/pl.db`.
- [ ] **Gate 1:** Verify row count matches Wikipedia stats (~1.6M).
- [ ] **Gate 2:** Verify UTF-8 readability of category names.

### Phase 2: Graph Topology (Neo4j)
- [ ] **Gate 3:** Checksum verification of CSV outputs.
- [ ] **Implementation:** Create `core/tools/prepare_neo4j_csv.py` (QID-only).
- [ ] **Execution:** Generate `nodes.csv` and `edges.csv` from SQLite & `pagelinks`.
- [ ] **Import:** Use `neo4j-admin import`.

## 🔮 Future
- [ ] Phase 3: Enhanced Algorithms (Category Similarity).
- [ ] Phase 4: Full-Text Backfill (Lazy Loading).