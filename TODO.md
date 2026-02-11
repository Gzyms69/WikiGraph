# WikiGraph Tasks

## 🛡️ Fail-Safe Pipeline (Current Priority)
### Phase 8: Hybrid AI Engine (ACTIVE)
- [ ] **Gate 8.1:** Implement `AIService` provider pattern (Modular Local/Cloud).
- [ ] **Gate 8.2:** Integrate Gemini 1.5 Flash for relationship summarization.
- [ ] **Gate 8.3:** Create `/api/v1/ai/insight` endpoint.
- [ ] **Gate 8.4:** Add "AI Summary" card to Frontend Node Details.

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
- [ ] Setup: Install google-generativeai and set GEMINI_API_KEY in .env.
- [ ] Service: Create app/services/ai_service.py.
    - [ ] Function generate_node_insight(node_title, neighbor_titles).
    - [ ] Implement error handling (try/except for API quotas).
- [ ] Endpoint: Create app/api/routers/ai.py.
    - [ ] POST /explain: Accepts QID, returns text summary.

## Priority 2: AI User Interface (Frontend)
- [ ] UI Component: Create src/components/nebula/AIInsightCard.tsx.
    - [ ] State: idle | loading (skeleton) | success | error.
    - [ ] Trigger: Auto-load when Node Details opens OR "Ask AI" button (saves quota).
- [ ] Integration: Connect NodeDetailsPanel to the new AI endpoint.

## Priority 3: Data Robustness (The Glue)
- [ ] Wikipedia Fallback: Modify MetadataManager in backend.
    - [ ] If sqlite_result is None: Call https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title}.
    - [ ] Return live data formatted as local data.
