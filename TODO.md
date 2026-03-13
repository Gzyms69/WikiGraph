# WikiGraph -- Master Task List

Last Updated: 2026-03-13
Source: Technical Audit Report (wikigraph_audit_report.md)

This document is structured into three sections:
1. **Section A** -- Improvements to existing code (pre-AI hardening)
2. **Section B** -- AI integration plan (post-hardening)
3. **Section C** -- Archive of completed work

---

# SECTION A: PRE-AI HARDENING

Everything below must be completed BEFORE starting AI integration.
These tasks fix weaknesses identified in the technical audit and raise
the project's portfolio score from ~6.8/10 to ~8.5/10.

---

## A.1 Testing Infrastructure (CRITICAL -- Priority 1)

Current state: ad-hoc validation scripts, no pytest, no CI/CD.
Audit score: 2/10 (Portfolio), 3/10 (Code Quality).
Target: pytest framework + GitHub Actions CI pipeline.

- [ ] **A.1.1** Install and configure pytest
    - Add `pytest`, `pytest-asyncio`, `pytest-cov` to `requirements.txt`
    - Create `pytest.ini` at project root with `testpaths = tests`
    - Create `tests/conftest.py` with shared fixtures (SQLite test DB, mock Neo4j driver)

- [ ] **A.1.2** Write unit tests for core pipeline modules
    - `tests/unit/test_sqlite_loader.py` -- test table creation, encoding fix, index creation
    - `tests/unit/test_prepare_neo4j_csv.py` -- test NS=0 filtering, edge deduplication, checksum logic
    - `tests/unit/test_extract_infoboxes.py` -- test regex pre-check, JSON serialization, checkpoint resume
    - Minimum 3 test functions per file (happy path, edge case, error case)

- [ ] **A.1.3** Write integration tests for API endpoints
    - `tests/integration/test_health.py` -- GET `/api/v1/health` returns 200
    - `tests/integration/test_search.py` -- GET `/api/v1/search/{lang}?q=...` returns results
    - `tests/integration/test_entity.py` -- GET `/api/v1/entity/{lang}/{qid}` returns metadata
    - `tests/integration/test_ai.py` -- POST `/api/v1/ai/analyze` returns insight (mock provider)
    - Use `httpx.AsyncClient` with `app` fixture from `conftest.py`

- [ ] **A.1.4** Configure GitHub Actions CI
    - Create `.github/workflows/ci.yml`
    - Steps: checkout, setup Python 3.12, install deps, run `pytest --cov=app --cov=core`
    - Add coverage badge to `README.md`
    - Trigger on push to `main` and on pull requests

- [ ] **A.1.5** Archive old validation scripts
    - Move `tests/gate6_validation.py`, `tests/stress_test_*.py`, etc. to `tests/archive/legacy/`
    - Add a `tests/archive/README.md` explaining these are historical validation scripts

---

## A.2 Environment and Setup Hardening (Priority 2)

Current state: `setup_environment.sh` works on happy-path but is fragile.
Audit score: 5/10 (Functionality), 4/10 (Portfolio).

- [ ] **A.2.1** Add version validation to `setup_environment.sh`
    - Check Python version >= 3.10: `python3 -c "import sys; assert sys.version_info >= (3,10)"`
    - Check Node.js version >= 18: `node -v | grep -E "v(1[89]|[2-9][0-9])"`
    - Print clear error messages with installation links on failure

- [ ] **A.2.2** Create `.env.example` at project root
    - Include all required variables with comments:
      ```
      # Required: Google Gemini API key for AI insights
      GEMINI_API_KEY=your_key_here
      # Optional: AI provider selection (gemini | mock)
      AI_PROVIDER=mock
      # Optional: Neo4j credentials (defaults shown)
      NEO4J_USER=neo4j
      NEO4J_PASSWORD=wikigraph
      ```

- [ ] **A.2.3** Create required directories automatically
    - Add to `setup_environment.sh`: `mkdir -p data/raw logs data/neo4j_data`
    - Ensure the script creates per-language directories if `config/infrastructure.yaml` exists

- [ ] **A.2.4** Add "System Requirements" section to `README.md`
    - Minimum RAM: 8GB (16GB recommended for GDS algorithms)
    - Disk space: 30GB per language (dumps + SQLite + Neo4j data)
    - Required external tools: Docker, aria2c (optional but recommended)
    - Python >= 3.10, Node.js >= 18

---

## A.3 Backend Code Cleanup (Priority 3)

Current state: functional but has "work in progress" code in production.
Audit score: 6/10 (Code Quality) for Backend API.

- [ ] **A.3.1** Clean up `neo4j_manager.py` timeout implementation
    - Remove deliberation comments (lines 74-148 are 75 lines of "thinking out loud")
    - Replace with a clean implementation using `session.execute_read()` with `timeout` parameter
    - If timeout feature is not needed yet, remove it entirely and add a TODO comment (1 line, not 75)

- [ ] **A.3.2** Extract credentials to environment variables
    - Move `auth=("neo4j", "wikigraph")` from `neo4j_manager.py:32` to `.env` / `config.py`
    - Reference via `settings["neo4j_user"]` and `settings["neo4j_password"]`

- [ ] **A.3.3** Restrict CORS origins
    - Replace `allow_origins=["*"]` in `main.py` with a configurable whitelist
    - Default: `["http://localhost:3000"]` for development
    - Load from `.env` variable `CORS_ORIGINS` (comma-separated)

- [ ] **A.3.4** Add rate limiting to AI endpoint
    - Install `slowapi` package
    - Apply rate limit to `/api/v1/ai/analyze` (e.g., 10 requests/minute per IP)
    - Return 429 with descriptive message when exceeded

- [ ] **A.3.5** Remove or deprecate V0 legacy API
    - Option A: Remove the 4 legacy routers from `main.py` (lines 53-56)
    - Option B: Add `Deprecation` response header to all V0 endpoints
    - Update `README.md` to reflect V1-only API

---

## A.4 Frontend Code Cleanup (Priority 4)

Current state: visually impressive but has TypeScript and architectural issues.
Audit score: 6/10 (Code Quality) for Frontend.

- [ ] **A.4.1** Extract `API_BASE` to environment variable
    - Create or update `frontend/.env.local` with `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`
    - Replace hardcoded `API_BASE` in `WikiNebula.tsx:20` and `NodeDetailsPanel.tsx:12`
    - Use `process.env.NEXT_PUBLIC_API_URL` everywhere

- [ ] **A.4.2** Replace `any` types with proper TypeScript types
    - `fgRef = useRef<any>(null)` -- use type from `react-force-graph-3d` or create interface
    - `node: any` callbacks in ForceGraph3D props -- use `GraphNode` type
    - `link: any` callbacks -- create `GraphLink` interface
    - Target: zero `any` in `WikiNebula.tsx`

- [ ] **A.4.3** Add Error Boundary around ForceGraph3D
    - Create `frontend/src/components/nebula/GraphErrorBoundary.tsx`
    - Wrap `<ForceGraph3D>` in the error boundary
    - Show fallback UI: "Graph rendering failed. Click to retry."

- [ ] **A.4.4** Fix or remove dead code
    - `handleBulkRefresh` (WikiNebula.tsx:344) -- currently `console.log("disabled")`
    - Either implement the feature or remove the function and its UI button in `SettingsPanel.tsx`

- [ ] **A.4.5** Implement multi-language search
    - Current: search only queries `selectedLangs[0]`
    - Fix: `Promise.all(selectedLangs.map(lang => axios.get(...)))` and merge results
    - Add language badge to each search result so user knows which graph it comes from

---

## A.5 Pipeline Robustness (Priority 5)

Current state: works on happy-path, but lacks operational polish.

- [ ] **A.5.1** Add progress bars to long-running pipeline scripts
    - Install `tqdm` (already in requirements or add it)
    - `sqlite_loader.py` -- wrap main insert loop with `tqdm(total=estimated_rows)`
    - `prepare_neo4j_csv.py` -- wrap edge generation loop with `tqdm`
    - `extract_infoboxes.py` -- already has some progress, verify it shows ETA

- [ ] **A.5.2** Add summary logging to `prepare_neo4j_csv.py`
    - At end of execution, print: "Generated {X} nodes, {Y} edges, rejected {Z} orphan edges"
    - Log memory usage peak: `import tracemalloc; tracemalloc.get_traced_memory()`

- [ ] **A.5.3** Add edge deduplication to `prepare_neo4j_csv.py`
    - Before writing edges.csv, deduplicate on `(source_qid, target_qid)` using a set
    - Log how many duplicates were removed

- [ ] **A.5.4** Add SHA1 verification to `fetch_sql_dumps.py`
    - After downloading each file, fetch `{dump_url}/{lang}wiki/{date}/{lang}wiki-{date}-sha1sums.txt`
    - Compare computed SHA1 of downloaded file against expected hash
    - On mismatch: log warning and offer to re-download

- [ ] **A.5.5** Add failure logging to `extract_infoboxes.py`
    - Create `data/{lang}/bad_articles.log` with page_id and error message for every failed parse
    - At end of run, print summary: "Parsed {X} infoboxes, failed {Y} articles (see bad_articles.log)"

---

## A.6 DevOps and Deployment (Priority 6)

- [ ] **A.6.1** Add `docker-compose.yml` for Neo4j instances
    - Define services for each language (neo4j-pl, neo4j-de, neo4j-es)
    - Map ports from `config/infrastructure.yaml`
    - Keep `manage_containers.py` as alternative but document `docker-compose` as primary

- [ ] **A.6.2** Add PID file management to `dev.sh`
    - On start: write PID to `logs/backend.pid` and `logs/frontend.pid`
    - On stop: read PID file and `kill` specific process instead of `pkill -f`
    - On status: check if PID in file is still alive

- [ ] **A.6.3** Add log rotation
    - Option A: use `logrotate` config in `config/logrotate.conf`
    - Option B: truncate logs on restart in `dev.sh` (simpler)
    - Maximum log size before rotation: 50MB

---

# SECTION B: AI INTEGRATION PLAN

Prerequisites: All items in Section A marked as complete.
These tasks add the AI layer that transforms WikiGraph from a
Data Engineering project into an ML/AI Engineering portfolio piece.

---

## B.1 Phase 1: Semantic Search and Vector Embeddings (2-4 weeks)

Goal: Replace keyword-only FTS5 search with hybrid semantic search.
Portfolio value: adds "Vector Embeddings", "NLP Pipeline", "Hybrid Search" to CV.

### B.1.1 Text Extraction Pipeline
- [ ] **B.1.1.1** Evaluate data source for clean text
    - Option A (recommended): Download CirrusSearch JSON dumps from Wikimedia
      (`{lang}wiki-{date}-cirrussearch-content.json.gz`)
    - Option B: Extend `parser.py` to use `mwparserfromhell.strip_code()` on XML dumps
    - Decision criteria: CirrusSearch avoids Schema Drift entirely but requires new loader

- [ ] **B.1.1.2** Create CirrusSearch loader (if Option A chosen)
    - New file: `core/loaders/cirrus_loader.py`
    - Parse NDJSON format, extract `title`, `text`, `heading` fields
    - Store in SQLite table `articles_text(page_id INTEGER, section TEXT, content TEXT)`
    - Index: `CREATE INDEX idx_articles_text_page ON articles_text(page_id)`

- [ ] **B.1.1.3** Implement semantic chunker
    - New file: `core/pipeline/chunk_articles.py`
    - Chunking strategy: split by Wikipedia section headers (`== ... ==`), then by paragraphs
    - Max chunk size: 512 tokens (matching embedding model context window)
    - Each chunk stores metadata: `(page_id, qid, section_title, chunk_index, chunk_text)`
    - Store in SQLite table `article_chunks`

### B.1.2 Embedding Pipeline
- [ ] **B.1.2.1** Create embedding generation script
    - New file: `tools/ai/embed_articles.py`
    - Model: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions, multilingual)
    - Process: load chunks from SQLite -> batch encode (batch_size=256) -> store vectors
    - Add checkpoint support (resume from last processed chunk_id)
    - Estimated time: ~2-4 hours for 1.5M Polish articles on CPU

- [ ] **B.1.2.2** Integrate vector storage with SQLite
    - Option A (recommended): Use `sqlite-vec` extension for native vector search in SQLite
    - Option B: Use ChromaDB as separate vector database
    - Decision criteria: `sqlite-vec` keeps the stack simple (no new service to manage)
    - Create virtual table: `CREATE VIRTUAL TABLE vec_chunks USING vec0(embedding float[384])`

### B.1.3 Hybrid Search API
- [ ] **B.1.3.1** Create semantic search endpoint
    - New file: `app/api/v1/routers/semantic_search.py`
    - Endpoint: `GET /api/v1/search/semantic/{lang}?q=...&limit=10`
    - Logic: encode query with same model -> cosine similarity search in `vec_chunks`
    - Return: list of `{qid, title, score, matched_chunk_preview}`

- [ ] **B.1.3.2** Create hybrid search endpoint
    - Endpoint: `GET /api/v1/search/hybrid/{lang}?q=...&limit=10`
    - Logic: run FTS5 search AND semantic search in parallel
    - Merge results using Reciprocal Rank Fusion (RRF) scoring
    - Return: unified ranked results with source indicator (keyword/semantic/both)

- [ ] **B.1.3.3** Add semantic search to frontend
    - Update `SearchOverlay.tsx` to call hybrid endpoint instead of FTS5-only
    - Add toggle: "Keyword Search" / "Semantic Search" / "Hybrid"
    - Show relevance score and matched chunk preview in results

### B.1.4 Verification
- [ ] Write pytest tests for embedding pipeline (mock model, verify chunk storage)
- [ ] Write pytest tests for hybrid search endpoint (verify RRF merging logic)
- [ ] Run manual test: search "wynalazca zarowki" should return Edison/Swan articles
- [ ] Benchmark: measure search latency (target: < 200ms for hybrid search)

---

## B.2 Phase 2: GraphRAG with Text-to-Cypher (4-6 weeks)

Goal: Build conversational Q&A that traverses the knowledge graph to answer complex questions.
Portfolio value: adds "GraphRAG", "Agentic AI", "Text-to-Cypher" to CV.
Prerequisite: Phase B.1 complete (embeddings needed for context enrichment).

### B.2.1 Schema Enrichment (optional but recommended)
- [ ] **B.2.1.1** Add node type labels from Wikipedia categories
    - Script: `tools/ai/enrich_node_labels.py`
    - Logic: map top-level Wikipedia categories to node labels
      (e.g., "Category:Cities in Poland" -> `:City`, "Category:Polish physicists" -> `:Person`)
    - This enables richer Cypher queries beyond generic `:Concept` nodes
    - Store label mapping in SQLite `node_labels(qid TEXT, label TEXT)`

### B.2.2 Text-to-Cypher Engine
- [ ] **B.2.2.1** Design schema description prompt
    - Create `app/services/cypher_schema.py` that generates a text description of the Neo4j schema
    - Include: node labels, relationship types, available properties, example queries
    - This prompt is prepended to every Text-to-Cypher request

- [ ] **B.2.2.2** Implement Text-to-Cypher service
    - New file: `app/services/text2cypher_service.py`
    - Architecture: User question -> LLM generates Cypher -> validate query -> execute on Neo4j
    - Query validation: whitelist only READ operations (MATCH, RETURN, WHERE, ORDER BY, LIMIT)
    - Block: CREATE, DELETE, SET, MERGE, DETACH, DROP, CALL (except whitelisted GDS procs)
    - Add `LIMIT 100` to all generated queries (prevent full-graph scans)
    - Retry logic: if Cypher fails, send error message back to LLM for correction (max 2 retries)

- [ ] **B.2.2.3** Implement RAG context assembly
    - New file: `app/services/rag_context.py`
    - Logic:
      1. Execute validated Cypher query on Neo4j -> get result QIDs
      2. For each QID: fetch relevant text chunks from `article_chunks` (semantic search)
      3. Assemble context: graph results + relevant text chunks + node metrics
      4. Send assembled context to LLM for final answer generation
    - Apply token budget: max 4000 tokens of context per request

### B.2.3 Chat API and Frontend
- [ ] **B.2.3.1** Create chat endpoint
    - Endpoint: `POST /api/v1/chat/{lang}`
    - Request body: `{"message": "...", "session_id": "..."}`
    - Response: `{"answer": "...", "sources": [...], "cypher_query": "...", "confidence": 0.85}`
    - Store conversation history per session_id (in-memory or Redis)

- [ ] **B.2.3.2** Create chat frontend component
    - New file: `frontend/src/components/nebula/ChatPanel.tsx`
    - Features: message input, conversation history, source citations
    - Show generated Cypher query in expandable "How I found this" section
    - Highlight source nodes in the 3D graph when answer is displayed

### B.2.4 Verification
- [ ] Write pytest tests for Cypher validation (block dangerous queries)
- [ ] Write pytest tests for RAG context assembly (verify token budget)
- [ ] Manual test: "What are the most important cities in the Polish Wikipedia graph?"
- [ ] Manual test: "Which articles connect Poland to Germany?" (requires path traversal)
- [ ] Benchmark: end-to-end latency target < 5 seconds

---

## B.3 Phase 3: Graph Neural Networks (6-10 weeks, optional)

Goal: Train custom GNN models for link prediction, surpassing heuristic baselines.
Portfolio value: adds "PyTorch Geometric", "GNN", "Link Prediction", "Model Training" to CV.
Prerequisite: Phase B.1 complete (embeddings serve as node features).

### B.3.1 Data Preparation
- [ ] **B.3.1.1** Export graph to PyTorch Geometric format
    - New file: `tools/ai/export_pyg_graph.py`
    - Export from Neo4j/CSV: node list with features, edge list
    - Node features: concatenate pre-computed metrics (PageRank, degree, community_id)
      with text embeddings (384-dim from Phase B.1) -> total ~390 features per node
    - Save as PyG `Data` object (`.pt` file)
    - Handle memory: use subgraph sampling for graphs > 1M nodes (GraphSAGE NeighborLoader)

- [ ] **B.3.1.2** Create train/validation/test split
    - Remove 10% of edges for test, 5% for validation
    - Generate negative samples (node pairs with no edge) at same ratio
    - Save splits as separate files for reproducibility

### B.3.2 Model Training
- [ ] **B.3.2.1** Implement GCN/GAT link prediction model
    - New file: `tools/ai/train_link_prediction.py`
    - Architecture: 2-layer GCN or GAT with 128-dim hidden layers
    - Decoder: dot product between node embeddings
    - Loss: Binary Cross-Entropy on positive/negative edge pairs
    - Optimizer: Adam with learning rate scheduling

- [ ] **B.3.2.2** Train and evaluate
    - Training: run on GPU (Google Colab or local if available)
    - Track metrics: AUC-ROC, Average Precision, Hits@K (K=10,50,100)
    - Compare against baselines: Adamic-Adar, Jaccard (already computed in WikiGraph)
    - Save best model checkpoint with training curves

### B.3.3 Integration
- [ ] **B.3.3.1** Create inference endpoint
    - Endpoint: `GET /api/v1/ml/predict-links/{lang}/{qid}?limit=10`
    - Load trained model, compute embeddings for query node, predict top-K missing links
    - Return: `{predicted_links: [{qid, title, probability}, ...]}`

- [ ] **B.3.3.2** Add "Predicted Connections" card to frontend
    - New section in `NodeDetailsPanel.tsx` showing GNN-predicted links
    - Visual indicator comparing GNN predictions vs. heuristic (Jaccard) predictions

### B.3.4 Verification
- [ ] Publish training results as `docs/gnn_benchmark.md` with tables and plots
- [ ] Compare GNN AUC-ROC vs. Adamic-Adar AUC-ROC on same test set
- [ ] Manual test: verify predicted links are semantically reasonable

---

# SECTION C: COMPLETED WORK (Archive)

The following tasks have been completed in previous phases.
Preserved for historical reference and to demonstrate project evolution.

---

## Phase 8: Hybrid AI Engine (Completed)
- [x] Gate 8.1: Implement `AIService` provider pattern (Modular Local/Cloud)
- [x] Gate 8.2: Integrate Gemini 2.5 Flash for relationship summarization
- [x] Gate 8.3: Create `/api/v1/ai/insight` endpoint
- [x] Gate 8.4: Add "AI Summary" card to Frontend Node Details

## Phase 7: The Visualizer (Completed)
- [x] Gate 7.1: Legacy Frontend Cleanup
- [x] Gate 7.2: API Integration (Search, Nebula, Expansion)
- [x] Gate 7.3: 3D Visualization Restoration
- [x] Gate 7.4: Stabilization Audit (Fixed 32GB RAM Crash)

## Phase 6: Unified Backend API (Completed)
- [x] Restoration: Refactor `MetadataManager` to serve JSON infoboxes
- [x] Integration: Update `concept.py` to return rich node data
- [x] Search: Implement high-performance title search (FTS5)

## Phase 5: Language-Agnostic Architecture (Completed)
- [x] LanguageManager: Modernized with safe accessors and defaults
- [x] Core Pipeline: Refactored for infinite scalability (parser, loader, extractor)
- [x] Infrastructure: Dynamic container controller with hash-based port allocation
- [x] JIT Resurrection: Automated configuration for 300+ languages

## Sprint 8.0: Node Card Real-Metrics Upgrade (Completed)
- [x] Audit current NodeDetailsPanel.tsx metrics display
- [x] Replace `Connectivity` with actual PageRank value
- [x] Replace `Cluster 0` with real `louvain_id` from `/metrics/{lang}/{qid}`
- [x] Add missing metrics: Triangle Count, Authority Score
- [x] Compute and display Degree Centrality
- [x] Add tooltips explaining each metric (definition, meaning, formula)
- [x] Remove fake scaling formula `Math.min((node.val / 20) * 100, 100)`
- [x] Test with PL, ES, DE

## Sprint 8.1: Analytical AI Endpoints (Completed)
- [x] Create `app/services/ai_service.py` with abstract base, GeminiFlash, Mock
- [x] Add config vars `AI_PROVIDER`, `GEMINI_API_KEY`
- [x] Implement `analyze-node` endpoint
- [x] Register router in `app/api/v1/api.py`
- [x] Test with mock provider and Gemini Flash

## Sprint 8.2: Frontend AI UI (Completed)
- [x] Add "Analyze with AI" button in `NodeDetailsPanel.tsx`
- [x] Create `AIInsightCard.tsx` component
- [x] Implement `fetchAnalyzeNode` API call
- [x] Session caching for AI insights
- [x] Display all Tier 1 metrics (pagerank, triangle_count, auth_score, louvain_id, leiden_id, degree)
- [x] Differentiate Louvain vs Leiden with appropriate labels

## Incomplete items from previous sprints (carried forward to Section A/B)
- [ ] `compare-nodes` endpoint -- defer to Phase B.2 (GraphRAG)
- [ ] Two-node selection and "Compare" button in frontend -- defer to Phase B.2
- [ ] Wikipedia live data fallback (`rest_v1/page/summary`) -- defer to Phase B.1
- [ ] Hybrid Infobox Extractor (Templates + Tables) -- defer to Phase B.1 (CirrusSearch bypass)

## Deprecated / Superseded Tasks
The following tasks are superseded by the graph-grounded approach and will not be implemented:
- `POST /api/v1/ai/insight` (titles-only endpoint) -- replaced by dossier-based `/ai/analyze`
- `generate_node_insight(node_title, neighbor_titles)` -- context-poor, replaced by `_compile_dossier()`
