# WikiGraph 🌐

**High-Performance Wikipedia Graph Database Pipeline**

WikiGraph is a production-ready system for transforming massive Wikipedia XML dumps into a dual-database architecture: **SQLite** for metadata and search, and **Neo4j** for complex graph analysis and topology.

## 🚀 Features

- **Massive Scale Ingestion**: Handles 25GB+ XML dumps using streaming parallel parsing.
- **Hardware Optimized**: Utilizes multi-core CPUs and aggressive I/O smoothing to prevent system lockups.
- **Memory Hardened**: Zero-RAM link resolution ensures stability on consumer hardware (16GB+ RAM).
- **Multi-Language Core**: Dynamic support for Polish, German, and English datasets.
- **Graph Intelligence**: Fully implements Wikipedia Redirects/Aliases for a highly connected knowledge graph.

## 🏗️ Project Structure

```text
WikiGraph/
├── app/                  # Flask REST API
├── config/               # Multi-language YAML configurations
├── core/                 # Core logic: Parser, Loaders, Managers
│   ├── parser.py         # Parallel XML streaming parser
│   ├── sqlite_loader.py  # Zero-RAM SQLite database loader
│   ├── neo4j_loader.py   # High-speed parallel Neo4j loader
│   ├── redirect_loader.py# Alias/Redirect importer
│   └── database_manager.py # DB initialization and stats
├── data/                 # Data Storage
│   ├── raw/              # Wikipedia .bz2 dumps
│   ├── processed/        # Intermediate JSONL/CSV batches
│   └── db/               # SQLite database files
├── tools/                # Utility & Monitoring scripts
└── run_api.py            # API Entry point
```

## 🛠️ Requirements

- Python 3.8+
- Neo4j 5.x (with APOC plugin)
- ~100GB disk space for full multi-language processing
- 16GB+ RAM recommended

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

### 3. Pipeline Execution (Example: German)
```bash
# 1. Parse XML to batches
python3 core/parser.py --lang=de

# 2. Ingest to SQLite
python3 core/database_manager.py init
python3 core/sqlite_loader.py --lang=de

# 3. Ingest to Neo4j
python3 core/neo4j_loader.py --lang=de
python3 core/redirect_loader.py --lang=de
```

## 📊 Current Status
- **Polish (pl)**: 2.1M articles ingested.
- **German (de)**: 5.9M articles processed.
- **English (en)**: 25GB dump ready for processing.

--- 
*WikiGraph - Transforming Wikipedia into a professional knowledge graph.*