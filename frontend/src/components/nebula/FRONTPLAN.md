# WikiGraph Frontend: Technical Manual & Architecture

**Status:** Phase 8 (AI Intelligence) COMPLETED.

## 🗺️ Component Navigation Map
Use this map to navigate and update frontend functionality.

| UI Feature | Component File | Description |
| :--- | :--- | :--- |
| **3D Engine** | `src/components/WikiNebula.tsx` | Three.js/Force-Graph engine. Handles physics, interactions, and zoom-to-fit logic. |
| **Search System** | `src/components/nebula/SearchOverlay.tsx` | Floating search bar with real-time FTS5 suggestions and focus logic. |
| **Node Info Card** | `src/components/nebula/NodeDetailsPanel.tsx` | **Analytical Dashboard.** Displays PageRank, HITS, Clustering, Degree, and Communities. |
| **AI Insight Card** | `src/components/nebula/AIInsightCard.tsx` | **Narrative Intelligence.** Generates grounded summaries using Gemini 2.5 Flash. |
| **Initialization** | `src/components/nebula/InitializationScreen.tsx` | Startup screen for multi-language selection and active cluster discovery. |
| **Data Models** | `src/types/graph.ts` | TypeScript interfaces for Nodes, Links, and Analytical Metrics. |

---

## ⚙️ Core Features (Phase 8 Complete)

### 1. Advanced Analytical Dashboard
The `NodeDetailsPanel` has been upgraded from placeholders to a comprehensive analytical dashboard.
- **Metrics Display:** Uses a 2-column grid to show PageRank, Authority, Triangle Count, Degree (In/Out), Louvain, and Leiden.
- **Dynamic Tooltips:** Interactive info icons (ⓘ) provide formal definitions and mathematical formulas for every metric.
- **Data Fetching:** Implements an async fetcher targeting the `/graph/metrics` endpoint on every node selection.

### 2. AI-Powered Narrative Insights
The `AIInsightCard` provides on-demand structural analysis.
- **Intelligence:** Uses **Gemini 2.5 Flash** grounded in a "Structural Dossier" (Metrics + Metadata + Similarities).
- **Session Caching:** Implements a global `Map` cache to persist generated insights across the session, saving API costs.
- **Dynamic Labeling:** Automatically detects and displays the model name from the backend response.
- **Resilience:** Seamlessly degrades to structural mock insights if the Google API is rate-limited (429).

### 3. Navigation & Focus
- **Deep-Linking:** Node Card provides direct links to the source Wikipedia articles.
- **Neighborhood Expansion:** "Expand" button triggers weighted neighbor discovery in the 3D space.

---

## 📡 API Interaction Lifecycle

| Endpoint | Triggering Component | Usage |
| :--- | :--- | :--- |
| `/graph/languages` | `InitializationScreen.tsx` | Discovers available language containers on startup. |
| `/graph/metrics` | `NodeDetailsPanel.tsx` | Fetches the full analytical profile of a node. |
| `/ai/analyze` | `AIInsightCard.tsx` | POST request to generate narrative context for an entity. |
| `/search/{lang}` | `SearchOverlay.tsx` | Queries the SQLite FTS5 search engine. |
| `/weighted-neighbors` | `WikiNebula.tsx` | Fetches neighborhood expansion data. |

---

## 🛠️ System Stability & Performance

### 1. Memory Safety (Enforced)
- **RSS Limit:** 2GB (Enforced via `dev.sh`).
- **Baseline:** ~520MB RSS during 3D rendering.
- **Optimization:** Workspace isolation (renaming root `package.json`) prevents recursive build scanning and 32GB OOM crashes.

### 2. Implementation Principles
- **Tailwind CSS v4:** Theme variables defined in `globals.css`.
- **Async Safety:** All API calls use `axios` with proper loading/error states and skeleton loaders.
- **Singleton Pattern:** Backend AI services use `asyncio.Lock` to ensure thread-safe provider initialization.
