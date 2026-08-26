# WikiGraph

WikiGraph is a language-agnostic Knowledge Graph engine designed to process Wikipedia database dumps into a unified structure. It utilizes Neo4j for topological analysis and traversal, combined with SQLite for metadata storage and high-performance full-text search.

## System Architecture

WikiGraph implements a **Polyglot Persistence (Split-Storage) Architecture** specifically engineered to handle multi-gigabyte Wikipedia graphs without memory saturation. By strictly decoupling topology from textual content, the system ensures optimal RAM utilization across both graph traversals and full-text search.

```mermaid
flowchart TB
    subgraph Client["Presentation Layer (Client Browser)"]
        ThreeJS["Next.js 15 + Three.js (react-force-graph-3d)"]
        SpiralLayout["Phyllotaxis Spiral Layout (Golden Angle θ = i * 137.5°)"]
        Spotlight["Spotlight Subgraph Masking & Cubic Camera Easing"]
        ThreeJS --- SpiralLayout
        ThreeJS --- Spotlight
    end

    subgraph Bridge["Application Layer (FastAPI Virtual Bridge)"]
        Router["Strategic Async Router & Dependency Injection"]
        Pool["SQLAlchemy QueuePool (check_same_thread=False)"]
        GDS_Bridge["Neo4j Async Driver Pool (Per-Language Bolt)"]
        AI_Strat["AIService Strategy (Gemini 2.5 Flash / Mock Provider)"]
        Router --> Pool
        Router --> GDS_Bridge
        Router --> AI_Strat
    end

    subgraph Storage["Storage Layer (Polyglot Split-Storage)"]
        subgraph Neo4j_Engine["Neo4j 5 Community + GDS (Topology Only)"]
            Topology["Graph Topology: (:Concept {qid}) -[:LINKS_TO]-> (:Concept {qid})"]
            GDS_Projections["In-Memory GDS Projections (similarity-graph)"]
            SafetyValve["Cartesian Safety Valve (LIMIT 2000 Common Neighbors)"]
        end

        subgraph SQLite_Engine["SQLite 3.37+ (Metadata & Search)"]
            FTS5["SQLite FTS5 Full-Text Index (articles_fts: title, qid UNINDEXED)"]
            MetaDB["Relational Metadata: pages, link_targets, id_mapping"]
            MetricsKV["Materialized Metrics Table (node_metrics Key-Value)"]
        end
    end

    Client <-->|RESTful JSON / HTTP| Router
    GDS_Bridge <-->|Bolt Protocol (7687, 7688...)| Neo4j_Engine
    Pool <-->|run_in_executor (WAL Mode)| SQLite_Engine
```

### Architectural Principles

#### 1. Polyglot Split-Storage (Zero String Overhead in Graph)
*   **Neo4j (Topology Engine):** Stores **exclusively** Wikidata IDs (`qid`) and directed relationships (`LINKS_TO`). Textual titles, descriptions, and infoboxes are strictly prohibited in the graph database. This design keeps JVM heap usage minimal and maximizes pagecache efficiency for topological traversals (BFS, shortest path, PageRank).
*   **SQLite (Content & Full-Text Search):** Stores article titles, infoboxes (JSON), degree counters, and pre-computed graph metrics. Operates in Write-Ahead Logging (`WAL`) mode with `PRAGMA synchronous = OFF` for bulk operations, and serves full-text queries via an optimized `FTS5` virtual table with `qid UNINDEXED` to minimize indexing overhead.

#### 2. Unified Backend API (FastAPI Virtual Bridge)
The backend federates queries across isolated per-language containers and local SQLite databases:
*   **Non-Blocking SQLite I/O:** Synchronous SQLite operations run inside thread pool executors (`run_in_executor`) managed by `SQLAlchemy QueuePool` to prevent event-loop starvation.
*   **Hub Node Cartesian Protection:** Local similarity queries (Adamic-Adar, Resource Allocation) enforce a strict safety limit (`LIMIT 2000` common neighbors) in Cypher to prevent combinatorial explosions on supernodes (articles with >10,000 links).
*   **Parallel GDS Execution:** Jaccard similarities run via the Neo4j Graph Data Science (GDS) library (`gds.nodeSimilarity.filtered.stream`) executing multi-threaded C++ operations on in-memory graph projections.

#### 3. Procedural 3D Nebula (Next.js 15 & Three.js)
*   **Phyllotaxis Spiral Placement:** Language clusters are procedurally placed in 3D space using the Golden Angle formula ($\theta = i \times \pi(3 - \sqrt{5})$), maintaining distinct visual neighborhoods along the vertical axis.
*   **Custom D3 Physical Forces:** Introduces a custom `lang_cluster` D3 force that pulls nodes toward their respective language coordinate centers while standard charge and link forces resolve local collisions.
*   **Adaptive Camera Easing:** Node transitions utilize a cubic-ease-out curve ($1 - (1 - t)^3$) with dynamic target offset calculation to avoid camera clipping inside dense clusters.

#### 4. Just-In-Time (JIT) Language Configuration
WikiGraph supports all Wikimedia languages via dynamic configuration generation. If a requested language configuration is absent in `config/languages/`, the system queries Wikimedia's `siteinfo` API in real time (when `WIKIGRAPH_JIT_ENABLED=true`) to resolve namespace aliases, magic words, and localized infobox prefixes.

---

## Installation & Setup

Follow these steps to set up a production-ready environment from scratch.

### 1. System Requirements & Capacity Planning

Processing multi-million entity graphs requires dedicated hardware budgeting:
*   **Operating System:** Linux (Ubuntu 22.04 LTS recommended) or macOS. Native Linux Docker Engine is strongly recommended over Docker Desktop to eliminate the ~17GB VM virtualization and file-sharing overhead (`virtiofsd`).
*   **Host RAM:**
    *   **16GB Minimum:** Sufficient for Polish (`pl`) graph (~1.67M nodes, 99.9M edges).
    *   **32GB Recommended:** Required for German (`de`) graph (~3.1M nodes, 149M edges) or simultaneous multi-language GDS projections.
    *   **Memory Budget Breakdown:** JVM Heap: 4GB per Neo4j container | Pagecache: 4GB | GDS Off-Heap: 3–4GB per active projection | Next.js Frontend: clamped to 2GB RSS.
*   **Storage:** 30GB+ available SSD space per language (raw dumps, SQLite WAL databases, Neo4j transaction logs).
*   **Software Runtimes:**
    *   `python3` (3.10+)
    *   `node` (v18+) & `npm`
    *   `docker` (Native Engine) & `docker-compose`
    *   `aria2c` (recommended for high-speed multi-connection dump downloads)

### 2. Initial Setup
Clone the repository and initialize the environment. The setup script will create a Python virtual environment (`venv`), install dependencies, and prepare the frontend.

```bash
git clone https://github.com/Gzyms69/WikiGraph.git
cd WikiGraph
chmod +x setup_environment.sh dev.sh
./setup_environment.sh
```

### 3. AI Configuration (Optional)
To enable AI summaries and "Analyze with AI" features:
1.  Obtain a **Gemini API Key** from Google AI Studio.
2.  Edit your `.env` file:
    ```bash
    nano .env
    # Set GEMINI_API_KEY=your_key_here
    ```

---

## The Data Pipeline (Ingestion & ETL)

WikiGraph processes raw Wikipedia SQL/XML dumps through an optimized 4-stage pipeline. Replace `pl` (Polish) with your desired language code (`de`, `es`, `en`).

### Phase 1: Download & Parsing (Offline)
This step downloads raw Wikimedia dumps, constructs the metadata database in SQLite, and formats the topology into Neo4j-compatible CSVs.

```bash
# Activate python environment
source venv/bin/activate

# Run the Master Ingestor (Downloads dumps automatically)
python3 core/pipeline/ingest.py --lang pl --download
```
*Time Estimate: 10–30 mins.*

#### Sequence & Internal Mechanics:
1.  [`fetch_sql_dumps.py`](file:///home/gzyms/Dev%20Projects/WikiGraph/core/pipeline/fetch_sql_dumps.py): Downloads `page`, `pagelinks`, `redirect`, `linktarget`, and `page_props` dumps via `aria2c` (with automatic fallback to `urllib`).
2.  [`sqlite_loader.py`](file:///home/gzyms/Dev%20Projects/WikiGraph/core/loaders/sqlite_loader.py):
    *   Initializes SQLite schema with speed pragmas (`journal_mode = MEMORY`, `synchronous = OFF`, `cache_size = 200000`).
    *   **MediaWiki 1.39+ Schema Adaptation:** Translates modern `pagelinks` (which reference integer `pl_target_id`) via the `link_targets` table with strict `lt_namespace = 0` filtering to prevent link loss.
    *   Handles encoding drift (`latin1` to `utf-8` normalization) for title strings.
3.  [`extract_infoboxes.py`](file:///home/gzyms/Dev%20Projects/WikiGraph/core/pipeline/extract_infoboxes.py):
    *   **Regex Pre-Check:** Executes `quick_has_infobox()` string search, skipping 60–90% of AST parsing overhead on pages without infoboxes.
    *   **Parallel Extraction:** Distributes XML parsing across a `multiprocessing.Pool`.
    *   **Atomic Batch Updates:** Writes extracted JSON infoboxes to a temporary staging table (`infobox_temp`) before bulk-updating the `pages` table.
    *   **Checkpoint/Resume Engine:** Tracks processed titles to allow seamless resumption after interrupts (`SIGINT`).
4.  [`prepare_neo4j_csv.py`](file:///home/gzyms/Dev%20Projects/WikiGraph/core/pipeline/prepare_neo4j_csv.py):
    *   Loads in-memory ID mapping (`page_id -> qid`) and target maps.
    *   Executes two-pass filtering ensuring only article-to-article (`NS=0`) links are written, eliminating hanging edges.
    *   Applies row count and checksum validation gates prior to disk write.

### Phase 2: Graph Import (Neo4j Admin)
Bulk-imports generated CSVs into a fresh Neo4j database using the high-throughput administrative import tool:

```bash
./core/pipeline/run_neo4j_import.sh pl
```
*Time Estimate: 5–15 mins.*

### Phase 3: Analytical Metrics Pre-computation
Calculates global graph metrics using Neo4j Graph Data Science (GDS) and materializes them into SQLite for O(1) runtime lookups.

```bash
# 1. Start the Neo4j container
./dev.sh start pl

# 2. Compute metrics (PageRank, HITS Authority, Louvain, Leiden, Triangle Count)
python3 tools/analytics/compute_global_metrics.py --lang pl --algorithms pagerank,hits,louvain,leiden,triangleCount
```
*   **Projection Optimization:** The compute tool groups algorithms by orientation (`NATURAL` for PageRank/HITS, `UNDIRECTED` for Louvain/Leiden/Triangles), minimizing memory allocation overhead.
*   **Buffered Streaming:** Streams scores from GDS into SQLite `node_metrics` in 50,000-record batches.
*   **Guaranteed Cleanup:** Projection graphs are explicitly dropped (`gds.graph.drop`) upon completion to reclaim off-heap RAM.

### Phase 4: Runtime Warmup (Jaccard Similarity)
To enable real-time **Jaccard Similarity** (which evaluates 2-hop graph neighborhood intersections in parallel), project the graph into GDS memory:

```bash
python3 tools/ops/warmup_gds.py --lang pl
```
*Note: Consumes ~3–4GB off-heap RAM for Polish (99.9M edges).*

---

## Running the Application

Once data is loaded, launch the full stack.

```bash
# Start everything (Database + Backend + Frontend)
./dev.sh start all
```

*   **Frontend:** [http://localhost:3000](http://localhost:3000) - 3D Graph Explorer.
*   **Backend API:** [http://localhost:8000/docs](http://localhost:8000/docs) - Swagger UI.

### Managing Services
The `dev.sh` controller is the command center for the entire stack. It manages Docker containers, the Python backend, the Node.js frontend, tracks process groups via `setsid` and `.run/*.pid` files, and ensures strict memory hygiene.

| Command | Target | Description |
| :--- | :--- | :--- |
| `start` | `all` | Launches Databases, Backend, and Frontend in sequence. |
| `start` | `pl`, `de`, `es` | Starts the specific Neo4j language container and waits for Bolt liveness. |
| `start` | `backend` | Starts the FastAPI server (Port 8000) with healthcheck verification. |
| `start` | `frontend` | Starts Next.js (Port 3000) clamped to **2GB Memory Limit**. |
| `stop` | `all` | Terminates all services via PID process groups and kills running ingestion pipelines. |
| `restart` | `backend` | Fast graceful restart for API code changes. |
| `status` | - | Shows health and PID status of Containers, API, and Frontend. |
| `links` | - | Displays active URLs and dynamically mapped HTTP ports for all services. |

**Example:**
```bash
./dev.sh restart backend  # Apply Python changes
./dev.sh links            # Show active endpoints and Neo4j web consoles
./dev.sh status           # Verify process health
```

---

## AI Features

*   **Graph-Grounded Insight:** The `/api/v1/ai/analyze` endpoint generates node summaries grounded in mathematical metrics (e.g., "This node is central because its PageRank is X...").
*   **Resilience:** Automatically falls back to "Mock" insights if the API quota is exceeded.
*   **Caching:** Frontend caches insights per session to prevent redundant API calls.

---

## API Usage Guide

The API is served at `/api/v1`.

### 1. Discovery and Metadata

#### Discover Active Languages
Lists languages with active containers and configurations.
- **Endpoint:** `GET /graph/languages`
- **Example:** `curl "http://localhost:8000/api/v1/graph/languages"`

#### Global Nebula View
Returns a sample of high-importance nodes (PageRank) and their links.
- **Endpoint:** `GET /graph/nebula/{lang}?limit=150`
- **Example:** `curl "http://localhost:8000/api/v1/graph/nebula/pl"`

#### Search Entities
Find QIDs using title-based full-text search.
- **Endpoint:** `GET /search/{lang}?q={query}`
- **Example:** `curl "http://localhost:8000/api/v1/search/pl?q=Douglas"`

#### Resolve Entity Details
Get metadata (title, infobox) and a sample of topological neighbors.
- **Endpoint:** `GET /entity/{lang}/{qid}`
- **Example:** `curl "http://localhost:8000/api/v1/entity/pl/Q42"`

#### Cross-Language Comparison
Compare metadata for a single entity across multiple databases in parallel.
- **Endpoint:** `GET /compare/{qid}?langs={code1,code2}`
- **Example:** `curl "http://localhost:8000/api/v1/compare/Q42?langs=pl,de"`

### 2. Graph Algorithms

#### Pathfinding (Shortest Path)
Find the shortest unweighted path (BFS) between two concepts.
- **Endpoint:** `GET /graph/path/shortest/{lang}?from_qid={q1}&to_qid={q2}&max_depth=6`
- **Example:** `curl "http://localhost:8000/api/v1/graph/path/shortest/pl?from_qid=Q42&to_qid=Q64"`

#### Scored Neighbors (Similarity)
Find entities similar to a target node based on graph topology.
- **Supported Metrics:** `jaccard`, `resource_allocation`, `adamic_adar`.
- **Endpoint:** `GET /graph/neighbors/scored/{lang}/{qid}?metric={metric}&limit=20`
- **Example:** `curl "http://localhost:8000/api/v1/graph/neighbors/scored/pl/Q42?metric=jaccard"`

#### Node Metrics (Global Analytics)
Retrieve pre-computed metrics for a node.
- **Options:** Fetch all metrics or filter by a specific key using `?key=`.
- **Endpoint:** `GET /graph/metrics/{lang}/{qid}?key={key}`
- **Example (All):** `curl "http://localhost:8000/api/v1/graph/metrics/pl/Q42"`
- **Example (Single):** `curl "http://localhost:8000/api/v1/graph/metrics/pl/Q42?key=pagerank"`

#### AI Analysis
Generate a structural analysis of a node using Gemini 2.5 Flash.
- **Endpoint:** `POST /api/v1/ai/analyze/{lang}/{qid}`
- **Example:** `curl -X POST "http://localhost:8000/api/v1/ai/analyze/pl/Q42"`

---

## Operational Guidelines & Memory Safety

### 1. Memory Hygiene & Resource Clamping
*   **Workspace Isolation (Monorepo Guard):** Root-level `package.json` and `package-lock.json` are renamed to `.root_backup`. This prevents Next.js from detecting a monorepo root and recursively scanning 100GB+ parent directories (`data/`, `venv/`, `logs/`), which historically caused 32GB RAM + 8GB Swap system crashes.
*   **Frontend Heap Clamping:** `dev.sh` explicitly starts the frontend with `NODE_OPTIONS="--max-old-space-size=2048"`, ensuring Next.js never exceeds 2GB RSS.
*   **Neo4j JVM vs Off-Heap GDS:** Container heap is restricted to 4GB (`config/infrastructure.yaml`). In-memory GDS projections reside in off-heap memory and must be explicitly dropped when analysis completes:
    ```cypher
    CALL gds.graph.drop('similarity-graph', false)
    ```

### 2. Process Group Supervision
*   **PID Tracking:** Backend and frontend PIDs are recorded in `.run/backend.pid` and `.run/frontend.pid`.
*   **Process Groups:** Services are spawned in independent sessions (`setsid`). Stopping a service executes `kill -TERM -$pid`, guaranteeing that all child workers and build watchers are terminated cleanly without orphan leaks.

### 3. Cartesian Safety Valve on Hub Nodes
*   Standard Cypher queries computing 2-hop intersections on articles with tens of thousands of links ("United States", "Poland") suffer from combinatorial explosion ($O(N^2)$).
*   WikiGraph injects a strict `WITH p, common LIMIT 2000` clause into Adamic-Adar and Resource Allocation queries, bounding worst-case traversal latency under 3–5 seconds.

---

## Graph Theory & Metrics Guide

WikiGraph computes several classical graph metrics to help understand the structure of knowledge. Here is what they measure and why they matter.

### 1. Importance (Centrality)
Who are the "VIPs" of the network?

*   **PageRank:**
    *   **Concept:** A node is important if other important nodes link to it. It measures long-term, global influence.
    *   **Analogy:** A voting system where a vote from the President counts more than a vote from a random citizen.
    *   **Use Case:** Finding the most influential articles in Wikipedia (e.g., "United States", "Biology").

*   **HITS Authority:**
    *   **Concept:** Identifies high-quality information sources ("Authorities") and the lists that point to them ("Hubs").
    *   **Analogy:** In a library, the "Authorities" are the best books on a topic, and the "Hubs" are the best bibliographies that list those books.
    *   **Use Case:** distinguishing between a "List of Physicists" (Hub) and "Albert Einstein" (Authority).

### 2. Similarity (Relatedness)
How related are two concepts based on their connections?

*   **Jaccard Similarity:**
    *   **Concept:** Measures the overlap between two nodes' neighborhoods relative to their total size.
    *   **Formula:** `Intersection / Union`.
    *   **Analogy:** If you and I have 10 friends, and 8 of them are the same people, we are socially similar.
    *   **Use Case:** Finding broadly related broad topics (e.g., "Physics" and "Chemistry").

*   **Adamic Adar & Resource Allocation:**
    *   **Concept:** Similar to Jaccard, but gives more weight to **rare** shared neighbors. Sharing a common friend who knows *everyone* (like "United States") is less meaningful than sharing a friend who only knows a few people (like a specific "1995 Jazz Album").
    *   **Analogy:** Two people who both like "Breathing" aren't special. Two people who both like "Underwater Basket Weaving" definitely have a connection.
    *   **Use Case:** Finding specific, niche connections between entities.

### 3. Community Detection
*   **Louvain / Leiden:**
    *   **Concept:** Groups nodes that are more densely connected to each other than to the rest of the network.
    *   **Analogy:** Identifying social circles (family, work colleagues, bowling club) within a person's life.
    *   **Use Case:** Auto-categorizing articles into topics like " WWII Battles," "French Cities," or "Marvel Movies" without reading the text.

---

## Troubleshooting

*   **Neo4j Out of Memory (OOM):**
    *   If the import fails or Neo4j crashes, check your Docker memory settings.
    *   Edit `config/infrastructure.yaml` to adjust heap sizes (`neo4j_heap: 4G`).
*   **Frontend "Build Loop":**
    *   Ensure the root `package.json` is renamed to `.root_backup` (handled automatically) to prevent Next.js from scanning the entire drive.
    *   `dev.sh` enforces a 2GB memory limit on the frontend process.

---

## Project Roadmap

### Phase 7: The Visualizer (Completed)
*   **Language-Agnostic Frontend:** Modernized Next.js frontend with high-performance 3D graph explorer.
*   **Unified Bridge:** Visualization engine now fully powered by verified multi-language Graph Engine (FastAPI).
*   **Dynamic Discovery:** UI automatically adapts to active language containers.

### Phase 8: Hybrid AI Engine (Completed)
*   **Provider Pattern:** Modular AI service capable of switching between Cloud and Local backends.
*   **Generative Insights:** Real-time relationship summarization using the Gemini 2.5 Flash API.
*   **Analytic Grounding:** AI narratives are based on rigorous metrics (PageRank, Adamic-Adar) rather than hallucinated context.

### Future: Vector Search (Phase 9)
*   **ChromaDB Integration:** Implement a vector database to store semantic embeddings of Wikipedia articles.
*   **Semantic Search:** Extend the search API to support concept-based queries.

## License
GPLv3
