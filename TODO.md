# WikiGraph Tasks

## 🛡️ Fail-Safe Pipeline (Current Priority)
### Phase 8: Hybrid AI Engine (ACTIVE)
- [x] **Gate 8.1:** Implement `AIService` provider pattern (Modular Local/Cloud).
- [x] **Gate 8.2:** Integrate Gemini 2.5 Flash for relationship summarization.
- [x] **Gate 8.3:** Create `/api/v1/ai/insight` endpoint.
- [x] **Gate 8.4:** Add "AI Summary" card to Frontend Node Details.

### Phase 7: The Visualizer (COMPLETED)
- [x] **Gate 7.1:** Legacy Frontend Cleanup.
- [x] **Gate 7.2:** API Integration (Search, Nebula, Expansion).
- [x] **Gate 7.3:** 3D Visualization Restoration.
- [x] **Gate 7.4:** Stabilization Audit (Fixed 32GB RAM Crash).

### Phase 6: Unified Backend API (COMPLETED)
- [x] **Restoration:** Refactor `MetadataManager` to serve JSON infoboxes.
- [x] **Integration:** Update `concept.py` to return rich node data.
- [x] **Search:** Implement high-performance title search (FTS5).

### Phase 5: Language-Agnostic Architecture (COMPLETED)
- [x] **LanguageManager:** Modernized with safe accessors and defaults.
- [x] **Core Pipeline:** Refactored for infinite scalability (parser, loader, extractor).
- [x] **Infrastructure:** Dynamic container controller with hash-based port allocation.
- [x] **JIT Resurrection:** Automated configuration for 300+ languages.

## 🔮 Future
- [ ] Phase 1.2: Vector Search (ChromaDB Integration).
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

---
# WikiGraph Tasks - The AI Sprint Week

## Priority 1: AI Intelligence Layer (Backend)
- [x] Setup: Install google-generativeai and set GEMINI_API_KEY in .env.
- [x] Service: Create app/services/ai_service.py.
    - [x] Function generate_node_insight(node_title, neighbor_titles).
    - [x] Implement error handling (try/except for API quotas).
- [x] Endpoint: Create app/api/routers/ai.py.
    - [x] POST /explain: Accepts QID, returns text summary.

## Priority 2: AI User Interface (Frontend)
- [x] UI Component: Create src/components/nebula/AIInsightCard.tsx.
    - [x] State: idle | loading (skeleton) | success | error.
    - [x] Trigger: Auto-load when Node Details opens OR "Ask AI" button (saves quota).
- [x] Integration: Connect NodeDetailsPanel to the new AI endpoint.

## Priority 3: Data Robustness (The Glue)
- [ ] Wikipedia Fallback: Modify MetadataManager in backend.
    - [ ] If sqlite_result is None: Call https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title}.
    - [ ] Return live data formatted as local data.

---

## 🔴 IMMEDIATE: Node Card Real‑Metrics Upgrade (Sprint 8.0) - [DONE]
- [x] **Audit current NodeDetailsPanel.tsx metrics display** – confirm which data sources are used.
- [x] **Replace `Connectivity`** with actual PageRank value (remove cap, relabel to "Global Importance").
- [x] **Replace `Cluster 0`** – fetch real `louvain_id` from `/metrics/{lang}/{qid}` and display it.
- [x] **Add missing metrics** from `/metrics` endpoint: Triangle Count, Authority Score.
- [x] **Compute and display Degree Centrality** – use neighbor count from `/entity/{lang}/{qid}`.
- [x] **Add tooltips** explaining each metric on hover (definition, meaning, and calculation formula).
- [x] **Remove fake scaling formula** `Math.min((node.val / 20) * 100, 100)`.
- [x] **Test with PL, ES, DE** – verify metrics are fetched correctly.

## 🧠 Sprint 8.1 – Analytical AI Endpoints (Backend) - [DONE]
- [x] **Create `app/services/ai_service.py`** with abstract base, GeminiFlash, Mock.
- [x] **Add config vars** `AI_PROVIDER`, `GEMINI_API_KEY` to `app/core/config.py`.
- [x] **Implement `analyze-node` endpoint** in `app/api/v1/routers/ai.py`.
- [ ] **Implement `compare-nodes` endpoint**.
- [x] **Register router** in `app/api/v1/api.py`.
- [x] **Test with mock provider** – verify prompt construction and response.
- [x] **Test with Gemini Flash** (if API key available) – verify latency, error handling.

## 🎨 Sprint 8.2 – Frontend AI UI - [DONE]
- [x] **Add "Analyze with AI" button** in `NodeDetailsPanel.tsx`.
- [x] **Create `AIInsightCard.tsx`** component (loading skeleton, error, insight display).
- [x] **Implement `fetchAnalyzeNode`** API call to new endpoint.
- [ ] **Add two‑node selection state** and "Compare" button.
- [ ] **Implement `fetchCompareNodes`** API call.
- [x] **Integrate both features** with proper error handling and loading states.
- [x] **Session Caching:** Implement client-side caching for AI insights.

---

## 🧊 Deprecated / Superseded Tasks
The following previously planned AI tasks are **superseded** by the graph‑grounded approach above and should **not** be implemented:
- `POST /api/v1/ai/insight` (titles‑only endpoint)
- `generate_node_insight(node_title, neighbor_titles)` (context‑poor function)
- [x] **Display all Tier 1 metrics** – ensure `pagerank`, `triangle_count`, `auth_score`, `louvain_id`, `leiden_id`, and `degree` are rendered in NodeDetailsPanel.
- [x] **Differentiate Louvain vs Leiden** – show both IDs with appropriate labels (Coarse / Fine).
