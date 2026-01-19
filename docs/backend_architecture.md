# Backend Architecture (Phase 5)

## Overview
The Unified Backend API acts as a **Virtual Bridge**, federating queries across isolated language databases. It does not maintain its own state but orchestrates parallel queries to Neo4j containers.

## Components

### 1. Core (`app/core/`)
- **Config:** Loads `infrastructure.yaml` to discover available languages and ports.
- **Logging:** Centralized logging for cross-language query debugging.

### 2. Services (`app/services/`)
- **Neo4jManager:** A Singleton connection pool manager.
    - Maintains a dictionary of drivers: `{'pl': Driver, 'de': Driver}`.
    - Handles **Graceful Degradation**: If 'de' is down, 'pl' queries must still succeed.
    - **Routing:** Resolves `lang` code to specific driver.

### 3. Routers (`app/api/routers/`)
- **Health (`/health`):** Aggregates status from all drivers.
- **Graph (`/api/{lang}/graph`):** Routes standard graph queries to specific DB.
- **Unified (`/api/unified`):** The Virtual Bridge implementation. Broadcasts queries by QID and merges results.

## Data Flow
1. **Request:** `GET /api/unified/node/Q36`
2. **Router:** Calls `Neo4jManager.broadcast("MATCH ... {qid: 'Q36'} ...")`
3. **Manager:**
    - Spawns async tasks for `pl` (Port 7687) and `de` (Port 7688).
    - Catches connection errors per task (Degradation).
4. **Result:** Merges responses by QID.
5. **Response:** JSON with combined data.