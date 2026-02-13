# WikiGraph

WikiGraph is a language-agnostic Knowledge Graph engine designed to process Wikipedia database dumps into a unified structure. It utilizes Neo4j for topological analysis and traversal, combined with SQLite for metadata storage and high-performance full-text search.

## System Architecture

The project employs a hybrid database architecture optimized for large-scale graph operations:

### 1. Unified Backend API (FastAPI)
The backend acts as a virtual bridge, federating queries across isolated language containers. It provides a standard REST interface for pathfinding, similarity scoring, and metadata retrieval.

### 2. Neo4j (Topology Engine)
Each language operates in an isolated Neo4j instance.
- **Topology Only:** To minimize memory footprint, Neo4j stores only the Wikidata ID (QID) and the link structure.
- **Similarity Implementation:** Jaccard similarity is implemented via the Neo4j Graph Data Science (GDS) library (`gds.nodeSimilarity.filtered.stream`) for parallel execution. Resource Allocation and Adamic Adar use optimized Cypher queries with a safety valve to handle hub nodes.

### 3. SQLite (Metadata and Content)
Article titles, infoboxes, and pre-computed global metrics are stored in language-specific SQLite databases.
- **Search Implementation:** Utilizes SQLite FTS5 for sub-millisecond keyword and prefix matching.
- **Metrics Implementation:** Global metrics like PageRank and Louvain communities are pre-computed using GDS and stored in a Key-Value `node_metrics` table for O(1) retrieval at runtime.

### 4. 3D Visualization (Next.js)
A high-performance React-based frontend using `react-force-graph-3d` to visualize the knowledge nebula in real-time. The visualizer is fully language-agnostic and dynamically adapts to available backend data.

### 5. JIT Configuration System
WikiGraph supports all Wikipedia languages through a Just-In-Time (JIT) configuration system. If a language configuration is missing, the system dynamically fetches site information from the Wikimedia API to generate parsing rules. (Enable via `WIKIGRAPH_JIT_ENABLED=true`).

---

## Installation & Setup

Follow these steps to set up a production-ready environment from scratch.

### 1. Prerequisites
Ensure your system meets these requirements:
*   **OS:** Linux (Ubuntu 22.04+ recommended) or macOS.
*   **RAM:** 16GB minimum (32GB+ recommended for English/German graphs).
*   **Storage:** 100GB+ SSD space.
*   **Software:**
    *   `python3` (3.10+)
    *   `node` (v18+) & `npm`
    *   `docker` & `docker-compose`
    *   `curl`, `jq`, `unzip`

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

## The Data Pipeline (Ingestion)

WikiGraph processes raw Wikipedia SQL/XML dumps. You must run this pipeline to populate your local database. Replace `pl` (Polish) with your desired language code (`en`, `de`, `es`).

### Phase 1: Download & Parsing (Offline)
This step downloads raw dumps, loads metadata into SQLite, and generates CSVs for Neo4j.

```bash
# Activate python environment
source venv/bin/activate

# Run the Master Ingestor (Downloads dumps automatically)
python3 core/pipeline/ingest.py --lang pl --download
```
*Time Estimate: 10-30 mins (depending on download speed).*

Sequence:
1. `fetch_sql_dumps.py`: Downloads `page`, `pagelinks`, `redirect`, and `page_props` dumps.
2. `sqlite_loader.py`: Initializes SQLite schema and loads SQL dumps.
3. `extract_infoboxes.py`: Parses the XML `pages-articles` dump to extract structured JSON metadata.
4. `prepare_neo4j_csv.py`: Generates the node and edge CSV files for Neo4j.

### Phase 2: Graph Import (Neo4j)
Import the generated CSVs into a fresh Neo4j container.

```bash
./core/pipeline/run_neo4j_import.sh pl
```
*Time Estimate: 5-15 mins.*

### Phase 3: Analytical Metrics (The "Intelligence")
Calculate global graph metrics (PageRank, HITS, Louvain Communities) and store them in SQLite for the dashboard.

```bash
# 1. Start the Neo4j container
./dev.sh start pl

# 2. Compute metrics (PageRank, Louvain, Leiden, HITS, Clustering)
# Note: Ensure you have enough RAM.
python3 tools/analytics/compute_global_metrics.py --lang pl --algorithms pagerank,hits,louvain,leiden,triangleCount
```
*Time Estimate: 20-60 mins (Memory Intensive).*

### Phase 4: Runtime Warmup (Jaccard Similarity)
To enable the **Jaccard Similarity** feature (which uses GDS in-memory graphs), you must project the graph into memory.

```bash
python3 tools/ops/warmup_gds.py --lang pl
```
*Note: This consumes additional RAM (~2GB for Polish).*

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
```bash
./dev.sh stop all       # Stop everything
./dev.sh restart backend # Restart API only
./dev.sh status         # Check service health
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

## Operational Guidelines

### 1. Memory Management
The system requires careful allocation of physical and virtual memory.
- **Heap Allocation:** Individual containers are limited to 4GB.
- **GDS Projections:** Graph projections reside in off-heap memory. 
- **Cleanup Requirement:** GDS projections must be dropped after use:
  `CALL gds.graph.drop('similarity-graph')`

### 2. Development Control
Manage the stack using the `dev.sh` controller:
- `./dev.sh start <lang>`: Initialize a specific database.
- `./dev.sh stop all`: Terminate services and reclaim memory.
- `./dev.sh status`: Review active services.

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
