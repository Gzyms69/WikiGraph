# WikiGraph Lab 🌌

**WikiGraph** is a high-performance Knowledge Graph engine designed to visualize and analyze the interconnected structure of Wikipedia across multiple languages. It transforms raw Wikipedia dumps into a graph database (Neo4j), identifying "Concepts" that transcend language barriers, and provides a powerful API for graph algorithms (Shortest Path, PageRank, Community Detection) and a 3D visual frontend.

---

## 🚀 Quick Start

The entire environment is managed by the `dev.sh` control script.

### Prerequisites
- **Docker** (for Neo4j Database)
- **Python 3.10+** (for FastAPI Backend)
- **Node.js 18+** (for Next.js Frontend)

### 1. Start the Stack
This single command spins up Neo4j, the Backend API, and the Frontend.
```bash
./dev.sh start
```
*Wait for the green "Environment Ready!" message.*

### 2. Access Services
- **frontend:** [http://localhost:3000](http://localhost:3000) - 3D Nebula Visualization
- **Backend API:** [http://localhost:8000/docs](http://localhost:8000/docs) - Swagger UI
- **Neo4j Browser:** [http://localhost:7474](http://localhost:7474) - Database Query UI
  - **User:** `neo4j`
  - **Password:** `wikigraph`

---

## 🛠️ Development Workflow

Use the `./dev.sh` script for all common tasks.

| Command | Description |
| :--- | :--- |
| `./dev.sh start` | Starts Neo4j, Backend, and Frontend. Checks for existing containers. |
| `./dev.sh stop` | Stops the Backend and Frontend processes. Leaves Neo4j running. |
| `./dev.sh restart` | Stops and immediately restarts the Backend and Frontend. |
| `./dev.sh status` | Checks the health of all services. |
| `./dev.sh logs` | Tails the logs for both Backend and Frontend in real-time. |
| `./dev.sh clean` | **Destructive.** Stops everything, removes the Neo4j container, and deletes logs. |
| `./dev.sh import` | **Destructive.** Wipes the DB and runs the bulk CSV importer from `data/neo4j_bulk/`. |

---

## 📂 Project Structure

```text
/
├── dev.sh                  # Master control script
├── app/                    # FastAPI Backend
│   ├── main.py             # App entry point
│   ├── api.py              # Route definitions
│   ├── database.py         # Neo4j connection logic
│   └── routers/            # API Endpoints
│       └── graph.py        # Graph algorithms (Neighbors, Pathfinding)
├── frontend/               # Next.js 3D Frontend
│   └── src/components/     # React components (WikiNebula)
├── core/                   # Core Data Processing Logic
│   └── ingest.py           # XML/SQL parsing utilities
├── tools/                  # Verification & Debugging Scripts
│   ├── check_kielce_neighbors.py # Verifies neighbor relevance logic
│   └── verify_interlingual.py    # Checks concept alignment
├── data/                   # Data Storage (GitIgnored)
│   ├── neo4j_data/         # Mounted volume for Neo4j container
│   └── neo4j_bulk/         # Location for CSVs ready for import
├── archive/                # Deprecated/Legacy scripts
├── logs/                   # Process logs and PID files
└── requirements.txt        # Python dependencies
```

---

## 🧠 Key Features & Algorithms

### 1. Semantic Neighbor Ranking
The API uses a **Jaccard Similarity** approximation to rank neighbors. Instead of just showing random links, it prioritizes nodes that share a "local context" (Triangles).
- **Formula:** `Intersection / (Degree_A + Degree_B - Intersection)`
- **Benefit:** Filters out "global noise" (e.g., Dates, Years, generic Lists) and bubbles up relevant connections (e.g., "Kielce" -> "Holy Cross Province").

### 2. Interlingual Concepts
Nodes in the graph are `Concepts` (language-agnostic entities), which are linked to `Articles` (language-specific pages).
- **Structure:** `(Article:PL)-[:REPRESENTS]->(Concept)<-[:REPRESENTS]-(Article:EN)`
- **Benefit:** Allows analyzing the graph structure across languages simultaneously.

### 3. Graph Data Science (GDS)
We use Neo4j GDS for heavy lifting:
- **PageRank:** Identifying the most influential nodes.
- **Louvain Modularity:** Detecting communities and clusters.
- **Shortest Path:** Finding connections between disparate topics.

---

## 📥 Data Ingestion

To populate the graph, you need to parse Wikipedia dumps (XML/SQL) into CSVs.

1.  **Export CSVs:** Use `core/bulk_exporter.py` (or legacy scripts) to generate CSVs in `data/neo4j_bulk/`.
2.  **Import:** Run `./dev.sh import`. This will:
    - Stop the current database.
    - Run `neo4j-admin database import full`.
    - Restart the database.

---

## 📝 Configuration

- **Backend:** Configured via `app/config.py` (Env vars supported).
- **Frontend:** Configured via `frontend/.env.local`.
- **Database:** `dev.sh` sets hardcoded defaults for local dev (`neo4j/wikigraph`).
