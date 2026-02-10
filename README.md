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

### 4. JIT Configuration System
WikiGraph supports all Wikipedia languages through a Just-In-Time (JIT) configuration system. If a language configuration is missing, the system dynamically fetches site information from the Wikimedia API to generate parsing rules. (Enable via `WIKIGRAPH_JIT_ENABLED=true`).

---

## API Usage Guide

The API is served at `/api/v1`.

### 1. Discovery and Metadata

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

---

## Ingestion Pipeline

The ETL pipeline consists of an offline processing phase and an online import phase.

### 1. Master Ingestion (Offline)
The `ingest.py` script automates the retrieval and parsing of Wikipedia dumps:
```bash
python3 core/pipeline/ingest.py --lang <lang_code> --download
```
Sequence:
1. `fetch_sql_dumps.py`: Downloads `page`, `pagelinks`, `redirect`, and `page_props` dumps.
2. `sqlite_loader.py`: Initializes SQLite schema and loads SQL dumps.
3. `extract_infoboxes.py`: Parses the XML `pages-articles` dump to extract structured JSON metadata.
4. `prepare_neo4j_csv.py`: Generates the node and edge CSV files for Neo4j.

### 2. Neo4j Bulk Import (Online)
Data is loaded into the language container using the Neo4j Admin tool:
```bash
bash core/pipeline/run_neo4j_import.sh <lang_code>
```

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

## Project Roadmap

### Phase 7: AI & Vector Search (Upcoming)
*   **ChromaDB Integration:** Implement a vector database to store semantic embeddings of Wikipedia articles.
*   **Embedding Pipeline:** Create a tool to batch-process SQLite articles using Sentence Transformers (e.g., `all-MiniLM-L6-v2`).
*   **Semantic Search Endpoint:** Extend the search API to support concept-based queries (e.g., "films about time travel") alongside keyword search.

### Phase 8: RAG & Live Data
*   **Context Retrieval:** Develop an endpoint to generate high-quality context for LLMs by fusing vector search results with 1-hop topological neighbors.
*   **Live Bridge:** Implement a real-time fetcher for the Wikimedia API to serve up-to-the-minute data for volatile entities.

### Phase 9: Frontend Refactoring & Visualization
*   **Legacy Restoration:** Refactor the existing Next.js application to restore the 3D-force-graph visualization engine.
*   **Control Deck:** Port the legacy control interface, including multi-language toggles and algorithm weight sliders (Jaccard vs. PageRank).
*   **Unified Integration:** Connect the frontend to the live Virtual Bridge API to enable real-time exploration of the global graph.

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

## Project Roadmap (Fast Track)

### Phase 7: The Visualizer (In Progress)
*   **Legacy Refactoring:** Modernizing the Next.js frontend to focus on a high-impact 3D graph explorer.
*   **Live Integration:** Connecting the visualization engine to the verified multi-language Graph Engine.

### Phase 8: Hybrid AI Engine
*   **Provider Pattern:** Implementing a modular AI service capable of switching between Cloud and Local backends.
*   **Generative Insights:** Real-time relationship summarization using the Gemini 1.5 Flash API.
*   **Offline Support:** Future-proof architecture for local LLM integration (Llama 3 via Ollama).

## License
GPLv3
