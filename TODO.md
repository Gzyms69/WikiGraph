# WikiGraph Tasks

## 🛡️ Fail-Safe Pipeline (Current Priority)
### Phase 1: Metadata Extraction (Metadata)
- [x] **Gate 0:** Validate `mwsql` library capabilities (Passed).
- [x] **Implementation:** Refactor `core/sqlite_loader.py` to use `mwsql` and support per-language DBs.
- [x] **Execution:** Run import for Polish (`pl`) into `data/db/pl.db`.
- [x] **Gate 1:** Verify row count matches Wikipedia stats (~1.6M).
- [x] **Gate 2:** Verify UTF-8 readability of category names.

### Phase 2: Graph Topology (Neo4j)
- [x] **Gate 3:** Checksum verification of CSV outputs.
- [x] **Implementation:** Create `core/tools/prepare_neo4j_csv.py` (QID-only).
- [x] **Execution:** Generate `nodes.csv` and `edges.csv` from SQLite & `pagelinks`.
- [x] **Import:** Use `neo4j-admin import`.

### Phase 2.5: Metadata Enrichment (Infoboxes)
- [x] **Extraction Tool:** Optimized `extract_infoboxes.py` with regex/multiprocessing.
- [x] **German (DE):** 1.9M records extracted (62% yield).
- [x] **Polish (PL):** 1.3M records extracted (79% yield).
- [x] **Validation:** Data integrity and cross-language overlap verified.

### Phase 5: Language-Agnostic Architecture (COMPLETED)
- [x] **LanguageManager:** Modernized with safe accessors and defaults.
- [x] **Core Pipeline:** Refactored for infinite scalability (parser, loader, extractor).
- [x] **Infrastructure:** Dynamic container controller with hash-based port allocation.
- [x] **JIT Resurrection:** Automated configuration for 300+ languages.

### Phase 6: Unified Backend API
- [ ] **Restoration:** Refactor `MetadataManager` to serve JSON infoboxes.
- [ ] **Integration:** Update `concept.py` to return rich node data.
- [ ] **Search:** Implement high-performance title search (FTS5 or Lucene).

## 🔮 Future
- [ ] Phase 3: Enhanced Algorithms (Category Similarity).
- [ ] Phase 4: Full-Text Backfill (Lazy Loading).
## [Future] Data Pipeline Enhancements
- [ ] **Hybrid Infobox Extractor:**
    - Implement a dual-pipeline extractor to handle both Templates ('{{...}}') and Manual Tables ('{| class="infobox"... |}').
    - Required for capturing data for major entities like *Berlin* (DE).
- [ ] **Universal Template Discovery:**
    - Create a tool to scan 10k random articles and rank template usage.
    - Use data to auto-generate 'language.yaml' configs instead of manual curation.
- [ ] **Error Recovery:**
    - Capture and log parsing failures for specific pages to a 'failures.db' for analysis.
