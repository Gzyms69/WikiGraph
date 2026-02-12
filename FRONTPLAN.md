# WikiGraph Frontend: Technical Manual & Audit Report

## 🗺️ Component Navigation Map
Use this map to navigate and update frontend functionality.

| UI Feature | Component File | Description |
| :--- | :--- | :--- |
| **3D Engine** | `src/components/WikiNebula.tsx` | The "Command Center". Manages 3D canvas, graph state, and engine tick. |
| **Node Info Card** | `src/components/nebula/NodeDetailsPanel.tsx` | Displays Entity name, QID, Connectivity %, Cluster ID, and Wiki links. |
| **Search System** | `src/components/nebula/SearchOverlay.tsx` | Floating search bar with real-time result dropdown. |
| **Settings Overlay** | `src/components/nebula/SettingsPanel.tsx` | Configures Hybrid Ranking weights (PageRank, Jaccard, etc.) and Force strengths. |
| **Bottom Controls** | `src/components/nebula/ControlDeck.tsx` | Play/Pause physics, Auto-rotate, Reset Camera, and Toggle Cluster coloring. |
| **Initialization** | `src/components/nebula/InitializationScreen.tsx` | First-run screen for language selection and cluster discovery. |
| **HUD / Stats** | `src/components/nebula/NebulaInfo.tsx` | Top-left logo and bottom-left "Active Node" counter. |
| **Shared Logic** | `src/utils/colors.ts` | Centralized color hashing logic for languages. |
| **Data Models** | `src/types/graph.ts` | TypeScript interfaces for Nodes and Links. |

---

## ⚙️ Functional Deep-Dive

### 1. Node Card & Interactivity
- **File:** `src/components/nebula/NodeDetailsPanel.tsx`
- **Functionality:** Triggered when a node is clicked in the 3D space. 
- **Calculations:** Connectivity is derived from `(node.val / 20) * 100`.
- **Actions:** Contains the "Expand" button (future feature) and "Wiki" external link.

### 2. The 3D Engine Tick
- **File:** `src/components/WikiNebula.tsx`
- **Method:** `onEngineTick` (wrapped in `useCallback`).
- **Logic:** Handles smooth camera transitions ("Flying") and custom clustering forces that pull nodes toward language-specific centers.

### 3. Search & Focus
- **File:** `src/components/nebula/SearchOverlay.tsx` -> `WikiNebula.tsx`
- **Flow:** Search selection calls `focusOnNode`, which checks if the node exists in the local graph. If not, it fetches neighbors from the API and spawns them dynamically.

---

## 📡 API Interaction lifecycle

| Endpoint | Triggering Component | Usage |
| :--- | :--- | :--- |
| `/graph/languages` | `InitializationScreen.tsx` | Discovers available language clusters on startup. |
| `/graph/nebula/{lang}` | `WikiNebula.tsx` | Fetches the initial high-importance nodes for the selected languages. |
| `/search/{lang}` | `SearchOverlay.tsx` | Queries the SQLite search engine via the backend. |
| `/weighted-neighbors` | `WikiNebula.tsx` | Fetches local neighborhood when a node is focused/expanded. |

---

## 🛠️ Audit Findings & System Stability

### 1. Runtime Memory Trace (Verified 300s Run)
- **Status:** **STABLE**
- **Baseline:** ~520MB RSS.
- **Limit:** 2GB (Enforced via `dev.sh`).
- **Outcome:** The massive 32GB RAM crash has been resolved.

### 2. Root Cause & Fixes
- **Confirmed Cause:** Workspace Resolution Loop. Next.js detected the root `package.json` and scanned the entire 100GB+ project tree (including `data/` and `venv/`) on every module resolution warning.
- **Implemented Fixes:**
    - **Isolation:** Renamed root `package.json` to `.root_backup`.
    - **Hardening:** Updated `dev.sh` with `NODE_OPTIONS` and liveness checks.
    - **Cleanup:** Refactored `InitializationScreen.tsx` to remove duplicate code.
    - **CORS:** Added `CORSMiddleware` to `app/main.py` to allow frontend communication.

---

## 📋 Developer Checklist for Updates
- [ ] **Styles:** Uses **Tailwind CSS v4**. Check `globals.css` for theme variables.
- [ ] **State:** Keep UI state local to components unless needed by the engine; lift up to `WikiNebula` for engine-linked logic.
- [ ] **Verification:** Always run `npm run build` in `frontend/` after changes to verify Turbopack resolution.

---
# Frontend Evolution Plan: Community Naming & UX

## 🏷️ Community Detection & Labeling Strategy
To resolve the "Cluster 0" anonymity, we will implement a 3-step automation pipeline:

### Krok 1: Algorytm Detekcji
- Ensure Louvain/Leiden is active in Neo4j GDS.
- Write communityId to nodes.

### Krok 2: Ekstrakcja Reprezentantów
- For each cluster, identify Top 5 nodes by PageRank.
- This provides the "semantic core" of the community.

### Krok 3: Automatyczne Generowanie Etykiet (Hybrid)
- **Option A (Fast):** Name cluster after the top PageRank node ("Cluster: [TopNode] & others").
- **Option B (Quality):** LLM Batch labeling using Gemini Flash.
- **Action:** Implement script `scripts/label_communities.py` to populate a `ClusterMeta` table.

## 🎨 UX & Architecture Recommendations

### 1. Visualization of Metrics
- Replace raw % Connectivity with "Importance" badges based on PageRank/HITS.
- Use metrics to scale node sizes in the 3D space.

### 2. Pathfinding Mode
- Add `isSelectingPath: boolean` state to UI.
- Allow clicking two nodes to trigger the Shortest Path endpoint.

### 3. AI Insight Integration
- Add an "AI Analysis" card to `NodeDetailsPanel.tsx`.
- Implement skeleton loaders for streaming Gemini responses.

### 4. Architecture: Global State
- **Recommendation:** Introduce **Zustand** for global graph state (selected nodes, path mode).
- Reduces prop-drilling between Search, Details, and the 3D Engine.

### 5. Color Legend
- Add a dynamic legend to `NebulaInfo` explaining cluster colors.

---

## Node Card Metrics Audit & Redesign (Feb 12, 2026)

### 🔍 Audit Findings (from frontend investigation)

| UI Label     | Data Source  | Reality                                                       |
|--------------|--------------|---------------------------------------------------------------|
| `Connectivity` | PageRank     | Scaling Error: Caps at 100% too early; conceptually misnamed. |
| `Cluster 0`    | API Hardcode | Placeholder: Not linked to real `leiden_id` in SQLite.        |
| `Importance`   | PageRank     | Correctly used for sizing, but not explicitly labeled.        |

**Root Cause:**  
- `NodeDetailsPanel.tsx` uses `node.val` (PageRank) and scales it arbitrarily.  
- `/api/v1/graph/nebula` returns `"community": 0` – the service does not yet join community IDs.  
- Other metrics exist in `/metrics` endpoint but are not displayed.

### 🛠️ Redesign Plan (Sprint 8.0)

1. **Eliminate fake metrics** – remove the `Connectivity` formula.  
2. **Display real metrics** – fetch `/metrics/{lang}/{qid}` and render:
   - PageRank (as `Global Importance`)
   - Triangle Count (as `Local Clustering`)
   - Authority Score (as `Authority`)
   - Louvain/Leiden ID (as `Community`)
3. **Compute Degree Centrality** – use neighbor count from `/entity/{lang}/{qid}`.  
4. **Add tooltips** – explain each metric on hover (definition, meaning, and calculation formula).  
5. **Preserve node sizing** – keep `Math.max(Math.sqrt(n.val || 0) * 2, 2)` (it correctly scales by PageRank).

**This upgrade requires zero backend changes – all data already exposed via existing endpoints.**

### 📈 Future Enhancement (Post‑Sprint 8.0)
- Join community names via `ClusterMeta` table (once automated labeling is implemented).
- Add sparkline visualisations for metric distributions.
