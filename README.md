# Polish Wikipedia Knowledge Graph

A professional-grade system for processing Polish Wikipedia dumps into a dual-database knowledge graph with web interface.

## Project Structure

```
WikiGraph/
├── .gitignore                 # Git ignore patterns
├── README.md                  # This file
├── requirements.txt           # Python dependencies
├── setup_environment.sh       # Environment setup script
├── run_api.py                 # Flask application entry point
├── app/                       # Web application logic
│   ├── api.py                # REST API endpoints
│   ├── models.py             # Database models and schema
│   ├── config.py             # Application configuration
│   ├── templates/            # HTML templates (Phase 4)
│   └── static/               # CSS/JS assets (Phase 4)
├── config/                    # Configuration management
│   ├── language_manager.py    # Centralized config loader
│   └── languages/            # Language-specific YAML configs (pl, en)
├── databases/                # SQLite databases
├── logs/                     # Logs and archived diagnostics
│   └── archive/              # Moved diagnostic outputs
├── processed_batches_*/      # Processed data batches (en, pl)
├── scripts/                  # Core processing and admin scripts
│   ├── manage_db.py          # Unified DB tool (Init/FTS/Stats)
│   ├── phase1_production.py  # Production XML parser
│   ├── load_multilang_data.py# Bulk data loader
│   ├── verify_multilang.py   # Data verification utility
│   ├── archive/              # Legacy and one-off scripts
│   └── tools/                # Maintenance utilities
└── venv_linux/              # Python virtual environment
```

## Quick Start

1. **Setup Environment:**
   ```bash
   chmod +x setup_environment.sh
   ./setup_environment.sh
   ```

2. **Initialize Database:**
   ```bash
   # Create base schema
   python3 scripts/manage_db.py init

   # View current database statistics
   python3 scripts/manage_db.py stats
   ```

3. **Run Production Processing:**
   ```bash
   # Parse XML dump into batches
   python3 scripts/phase1_production.py --lang=pl

   # Load batches into database
   python3 scripts/load_multilang_data.py --lang=pl
   ```

4. **Initialize Search & Start API:**
   ```bash
   # Build FTS5 search indexes (required for search)
   python3 scripts/manage_db.py init-fts

   # Start the Flask API server
   python3 run_api.py
   ```

## Development Phases

### Phase 1: Production Parser ✅
- ✅ Streaming XML parser with memory efficiency
- ✅ Link extraction and cleaning
- ✅ Batch processing with checkpointing
- ✅ Dual output: articles (JSONL) + links (CSV)

### Phase 2: Multi-Language Database Construction ✅
- ✅ SQLite database with composite keys (id, language)
- ✅ Multi-language support (pl, en) with unified schema
- ✅ Efficient two-pass loading with memory management
- ✅ Centralized database management utility (`manage_db.py`)

### Phase 3: Flask API & Multi-Language Support ✅
- ✅ RESTful API with search and article endpoints
- ✅ Configuration-driven multi-language support (`LanguageManager`)
- ✅ FTS5 virtual tables with diacritic-safe tokenization
- ✅ Standardized configuration with relative path support

### Phase 4: Frontend Development (In Progress)
- [ ] Flask templates for search and article views
- [ ] Interactive graph visualization (vis-network)
- [ ] Integrated search UI
- [ ] Responsive design with Bootstrap

### Phase 4: Frontend Development
- Flask templates for search and article views
- Interactive graph visualization (vis-network)
- Responsive design with Bootstrap

### Phase 5: Advanced Features
- Graph algorithms (PageRank, community detection)
- Shortest path queries
- Cross-language link analysis

## Key Features

- **Memory Safe**: Processes 2.6GB dump using streaming (no DOM loading)
- **Dual Database**: SQLite for articles, Neo4j for graphs
- **Scalable**: Batch processing with progress tracking
- **Professional**: Type hints, comprehensive error handling, logging

## Requirements

- Python 3.8+
- 19GB RAM (WSL configuration)
- Wikipedia dump: `plwiki-*-pages-articles-multistream.xml.bz2`

## Data Flow

1. **Raw Dump** → Streaming Parser → **Batch Files**
2. **Batch Files** → Database Loaders → **SQLite + Neo4j**
3. **Databases** → Flask API → **Web Interface**

## Validation Checklist

After running prototype:
- [x] 100 articles processed
- [x] Polish diacritics preserved
- [x] Links extracted and filtered
- [x] Memory usage < 500MB
- [x] JSONL output format correct

## API Documentation

The Flask API provides RESTful endpoints for querying the Wikipedia knowledge graph.

### Base URL
```
http://localhost:5000/api/
```

### Endpoints

#### GET /api/search
Full-text search across articles in a specific language.

**Parameters:**
- `q` (required): Search query string (2-100 characters)
- `lang` (optional): Language code, default 'pl' (available: 'pl', 'en')
- `limit` (optional): Maximum results, default 50 (max 50)
- `offset` (optional): Pagination offset, default 0

**Example Request:**
```bash
curl "http://localhost:5000/api/search?q=Warszawa&lang=pl&limit=10"
```

**Success Response (200):**
```json
{
  "results": [
    {
      "id": 123,
      "title": "Warszawa",
      "snippet": "Warszawa is the capital and largest city of <mark>Poland</mark>..."
    }
  ],
  "total": 45,
  "lang": "pl"
}
```

**Error Responses:**
- `400`: Missing/invalid parameters
- `500`: Server/database errors

### Running the API

1. **Initialize FTS Tables** (one-time setup, ~30-60 minutes for 2M articles):
   ```bash
   python3 scripts/manage_db.py init-fts
   ```

2. **Start Server:**
   ```bash
   python3 run_api.py
   ```

3. **Test Endpoints:**
   ```bash
   # Search Polish articles
   curl "http://localhost:5000/api/search?q=Warszawa&lang=pl"

   # Search English articles
   curl "http://localhost:5000/api/search?q=London&lang=en"

   # Pagination
   curl "http://localhost:5000/api/search?q=Python&limit=5&offset=10"
   ```

### Notes
- Search uses FTS5 virtual tables for fast full-text search on article titles
- Results include highlighted snippets with `<mark>` tags
- API includes CORS support for frontend integration
- All queries are parameterized to prevent SQL injection

## Performance Targets

- **Memory**: < 10GB peak for full processing
- **Time**: 6-12 hours for complete dump
- **Storage**: ~50GB for final databases
- **Links**: ~100M relationships expected

## Contributing

1. Follow the established directory structure
2. Use type hints and comprehensive error handling
3. Test with prototype before scaling
4. Keep memory usage monitored
