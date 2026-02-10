# WikiGraph: Project Context

## Purpose
WikiGraph is a system designed to process Wikipedia data (dumps) and build a large-scale graph representation (likely in Neo4j) to enable advanced queries like shortest path analysis between articles.

## Architecture & Key Technologies
- **Backend:** Python (FastAPI suggested by `run_api.py`)
- **Graph Database:** Neo4j (indicated by `core/engine/graph_engine.py` and `data/neo4j_data`)
- **Relational Database:** SQLite (indicated by `core/loaders/sqlite_loader.py`)
- **Data Processing:** Specialized tools for parsing Wikipedia XML/SQL dumps and cleaning import data.

## Key Files & Directories
- `app/`: API implementation (`api.py`, `models.py`).
- `core/`: Core logic for data ingestion, parsing, and graph management.
    - `pipeline/`: Active ELT scripts.
    - `loaders/`: Data parsers and database loaders.
- `core/engine/`: Neo4j schema setup and engine logic.
- `data/`: Raw and processed Wikipedia data.
- `tools/`: CLI tools for operations and analytics.
- `frontend/`: **Full-Stack Frontend.** The production Next.js application designed to connect to the Python/Neo4j backend.
- `website/`: **Static Demo Frontend.** A standalone Next.js application deployed to GitHub Pages. It simulates backend features (Search, Expansion) using `GraphService` and a pre-loaded JSON dataset (`demo-nebula.json`).

## Project Conventions
- Uses `requirements.txt` for dependency management.
- Includes a `setup_environment.sh` for initialization.
- Uses a `PROJECT_STATUS.md` to track progress (a custom convention for this project).

## Communication and Documentation Standards
- NEVER use emojis in documentation, logs, or communications.
- Always maintain a professional, human-like, and concise tone.
- Ensure all documentation is clear, accurate, and reflects the language-agnostic nature of the project.
- **DETAILED REPORTING MANDATE:** After completing a task, providing a shallow summary is forbidden. You MUST provide a comprehensive report including:
    1.  **Technical Implementation:** Detailed breakdown of code changes, including specific function names, algorithms (e.g., BFS), and logic flows.
    2.  **Files Modified:** A list of all files touched and the specific nature of the change.
    3.  **Verification Evidence:** Exact copies of test outputs, log messages, or command results that prove success.
    4.  **System Impact:** Analysis of how the change affects the broader system (e.g., performance, state, dependencies).
    5.  **Rationale:** Why specific technical decisions were made (e.g., "Used BFS for unweighted shortest path").

## Multilingual Wikipedia Strategy (Critical)

To ensure the system is truly language-agnostic, we must handle structural differences in Wikipedia data sources. Code **must not** hardcode "pl" or "en" defaults.

### 1. Parsing Differences
Languages differ in structural keywords. The `core/loaders/parser.py` relies on `config/language_manager.py` to provide these.

| Feature | English | Polish | German | Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **Namespace** | `Category:` | `Kategoria:` | `Kategorie:` | Use `siteinfo` to fetch local alias. |
| **Redirect** | `#REDIRECT` | `#PATRZ`, `#PRZEKIERUJ` | `#WEITERLEITUNG` | Check against list of magic words. |
| **File** | `File:`, `Image:` | `Plik:`, `Grafika:` | `Datei:` | Use `siteinfo` namespaces. |
| **Date Format** | `May 14, 2024` | `14 maja 2024` | `14. Mai 2024` | Use locale-specific parsers if extracting dates. |

### 2. Configuration Architecture
Currently, the system uses static YAML files in `config/languages/` (`pl.yaml`, `de.yaml`).
**Limitation:** This does not scale to all 300+ languages.
**Solution:** We need an `auto_config.py` tool.

### 3. Roadmap to Infinite Scalability
- [ ] **Dynamic Config Generator:** Create `core/legacy/fetch_lang_config.py` (to be revived in Pipeline) to query `https://{lang}.wikipedia.org/w/api.php?action=query&meta=siteinfo` and generate the YAML automatically.
- [ ] **Universal Parser:** Ensure `core/loaders/parser.py` loads this dynamic config.
- [ ] **Date Normalization:** Implement a strategy (e.g., `dateparser` library) to handle locale-specific date strings if extraction is required.

### 4. Implementation Rules
1.  **Never** iterate a hardcoded list `['pl', 'de']`. Use `data/raw` file scanning.
2.  **Never** assume `Category:` is the prefix. Use `LanguageManager.get_namespace_prefixes(lang)`.
3.  **Always** fail gracefully if a language config is missing (or attempt to fetch it).
## CRITICAL OPERATIONAL RULE
- **USER EXECUTION MANDATE:** I am STRICTLY FORBIDDEN from executing `./dev.sh` or any command that controls the full stack lifecycle directly. I must provide the command to the user and await their signal that it has been executed.
- **TASK REPORTING MANDATE:** I must always conclude my task execution with a detailed, structured report of what I did, what I found, and the final state of the system. This report serves as the authoritative record for the next interaction.
- **EXPLICIT PERMISSION MANDATE:** I am STRICTLY FORBIDDEN from starting any time-intensive or major task (data extraction, bulk imports, etc.) without explicit, turn-by-turn permission from the user. I must always present my plan and validation results first, then wait for an explicit "proceed" or "approve" command.
- **PRE-ACTION EXPLANATION MANDATE:** I MUST provide a clear, concise text explanation *before* executing any tool call (shell command, file write, replacement). I am forbidden from chaining tool calls without this intervening explanation. This ensures the user knows exactly what I am about to do and why. The format should be: "I will now [action] to [reason]."
- **HUMAN-IN-THE-LOOP MANDATE:** I must ALWAYS wait for an explicit "GO" before *any* tool use (including read-only tools), writing code, or performing any system actions.
- **CRITICAL EVALUATION MANDATE:** Every time I receive input from the User or DeepSeek (Coordinator), I must first provide a critical evaluation of the input and a detailed proposed plan for the next steps before requesting a "GO".
- **CRITICAL PROTOCOL:** I must ALWAYS wait for an explicit "GO" from the user before using ANY tool (including read-only ones) or writing code. I must also provide a critical evaluation and proposed plan after every user/coordinator message.

# CRITICAL TECHNICAL PROTOCOLS (2026-02-10 Update)

## 1. The GDS Mandate (Never Reinvent the Wheel)
*   **Rule:** For any graph algorithm (Similarity, Centrality, Pathfinding on weights), you MUST first check if a `gds.*` procedure exists.
*   **Reason:** Raw Cypher implementation of O(N^2) algorithms (like Jaccard/RA on 2-hop paths) causes Cartesian Explosions and crashes the database. GDS is optimized for parallel execution.
*   **Verification:** Run `CALL gds.list()` to verify availability before coding.

## 2. Memory & Projection Management
*   **Off-Heap Awareness:** GDS graphs live in **Off-Heap Memory**, distinct from the JVM Heap. Allocating 100% of RAM to Heap+Pagecache will cause OOM when GDS is used.
*   **Cleanup Mandate:** Any script or test that creates a GDS projection (e.g., `gds.graph.project`) MUST explicitly drop it (`gds.graph.drop`) upon completion or failure (try/finally block).
*   **Monitoring:** Use `free -h` and `docker stats` to track the *real* cost of graph projections.

## 🛡️ CORE SAFETY & EFFICIENCY DIRECTIVES (Post-Mortem 2026-02-10)

### 1. ANTI-REINVENTION PROTOCOL (GDS/APOC FIRST)
*   **Constraint:** NEVER write multi-hop pathfinding or set-similarity math in raw Cypher if a GDS procedure exists. 
*   **Checklist:** Run `CALL gds.list()` and `CALL apoc.help('keyword')` before implementing any logic that feels like "Standard Algorithm X".
*   **Reason:** Raw Cypher cannot optimize O(N^2) neighborhood set intersections effectively on Wiki-scale density.

### 2. RESOURCE CLEANUP & ORPHAN AUDIT
*   **Constraint:** Any container or background process started by Gemini must be tracked.
*   **Protocol:** Before declaring a task "Done," Gemini must check for lingering `while` loops, `monitor.log` writers, or unrelated background containers.
*   **Memory Hygiene:** GDS projections (`gds.graph.project`) must be dropped (`gds.graph.drop`) when the analysis is finished, unless explicitly requested to stay resident.

### 3. ZERO-NOISE MANDATE
*   **Constraint:** CLI warnings (e.g., Docker config errors) must be fixed before proceeding with development.
*   **Reason:** Environmental noise masks real errors (like `defunct connection`) and slows down diagnostic tools.
