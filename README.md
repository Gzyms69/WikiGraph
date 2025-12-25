# WikiGraph 🕸️

**Current Status:** 🟢 **STABLE / MULTI-LANG READY**

WikiGraph is a high-performance pipeline for ingesting massive Wikipedia XML dumps into a dual-database architecture: **SQLite** for relational metadata and search, and **Neo4j** for complex graph relationship analysis.

## 🚀 Recent Breakthroughs (Dec 2025)
- **Neo4j Integration:** Fully implemented graph database support with optimized parallel loaders.
- **High Performance:** Parallel link resolution (8+ cores) and aggressive memory caching (10GB+).
- **Redirect Awareness:** Added support for Wikipedia aliases (Redirects) to ensure high graph connectivity.
- **Multi-Language Core:** Dynamic support for Polish, English, and German Wikipedia dumps.

## 📊 Current Graph Scale [Polish Wikipedia]
| Metric | Count |
| :--- | :--- |
| **Article Nodes** | 2,105,331 |
| **Alias (Redirect) Nodes** | 583,883 |
| **Inter-Article Links** | 41,683,844 |
| **Alias Connections** | 583,883 |

## 🛠️ Architecture
WikiGraph uses a two-stage processing pipeline:
1.  **Stage 1 (Streaming Parser):** Uses `mwxml` to stream gigabytes of XML with <500MB RAM footprint, outputting compressed JSONL/CSV batches.
2.  **Stage 2 (Optimized Loaders):** 
    - **SQLite:** Stores full article metadata and FTS5 search indexes.
    - **Neo4j:** Stores the topological structure for pathfinding and hub analysis.

## 📦 Project Structure
```text
WikiGraph/
├── app/                  # Flask API & Business Logic
├── config/               # Multi-language YAML configs (pl, en, de)
├── databases/            # SQLite Storage
├── processed_batches/    # Intermediate data (jsonl.gz / csv.gz)
├── scripts/              
│   ├── phase1_production.py  # Streaming XML Parser
│   ├── load_multilang_data.py # Parallel SQLite Loader
│   ├── load_neo4j.py         # Parallel Graph Loader
│   └── extract_redirects.py  # Alias generator
└── venv_linux/           # Virtual Environment
```

## ⚡ Quick Start

### 1. Environment Setup
```bash
source venv_linux/bin/activate
pip install -r requirements.txt
```

### 2. Neo4j Setup (Docker)
```bash
docker run -d --name wikigraph-neo4j -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/wikigraph \
    -e NEO4J_PLUGINS='["apoc"]' \
    neo4j:5.14
```

### 3. Run Pipeline (Example: Polish)
```bash
# 1. Parse XML to batches
python3 scripts/phase1_production.py --lang=pl

# 2. Load SQLite (Search Engine)
python3 scripts/manage_db.py init
python3 scripts/load_multilang_data.py --lang=pl

# 3. Load Neo4j (Graph Engine)
python3 scripts/load_neo4j.py --lang=pl
python3 scripts/load_redirects_neo4j.py --lang=pl
```

## 🧪 Verification & Analytics
Run `python3 scripts/robust_verify.py` to analyze the graph structure, find major hubs, and test pathfinding between nodes.

---
*Maintained by Gzyms69. Last updated: Dec 25, 2025.*
