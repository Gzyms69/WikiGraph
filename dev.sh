#!/bin/bash

# WikiGraph Development Control Script
# Usage: ./dev.sh [start|stop|restart|status|logs|clean|import]

# --- Resolve Absolute Paths ---
# Get the absolute path to the directory where this script resides
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Configuration
FRONTEND_PORT=3000
BACKEND_PORT=8000
NEO4J_HTTP=7474
NEO4J_BOLT=7687

# Paths (Absolute)
LOG_DIR="$PROJECT_ROOT/logs"
API_LOG="$LOG_DIR/api_dev.log"
FRONT_LOG="$LOG_DIR/frontend_dev.log"
BACKEND_PID="$LOG_DIR/backend.pid"
FRONTEND_PID="$LOG_DIR/frontend.pid"
NEO4J_DATA_DIR="$PROJECT_ROOT/data/neo4j_data"

# Text Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Ensure Log Directory Exists
mkdir -p "$LOG_DIR"

# --- Helper Functions ---

function is_port_open() {
    lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null
}

function wait_for_port() {
    local port=$1
    local name=$2
    local retries=30
    echo -n "   Waiting for $name (Port $port)..."
    while ! is_port_open $port; do
        sleep 1
        echo -n "."
        ((retries--))
        if [ $retries -le 0 ]; then
            echo -e " ${RED}FAILED${NC}"
            return 1
        fi
    done
    echo -e " ${GREEN}OK${NC}"
    return 0
}

function check_neo4j_container() {
    if docker ps --format '{{.Names}}' | grep -q "^neo4j$"; then
        return 0 # Running
    elif docker ps -a --format '{{.Names}}' | grep -q "^neo4j$"; then
        return 2 # Exists but stopped
    else
        return 1 # Does not exist
    fi
}

# --- Main Commands ---

function start() {
    echo -e "${BLUE}🚀 Starting WikiGraph Lab Environment...${NC}"

    # 1. Start Neo4j
    check_neo4j_container
    neo4j_status=$?
    
    if [ $neo4j_status -eq 0 ]; then
        echo -e "${GREEN}✅ Neo4j is already running.${NC}"
    elif [ $neo4j_status -eq 2 ]; then
        echo -e "${YELLOW}📦 Neo4j container stopped. Starting...${NC}"
        docker start neo4j >/dev/null
    else
        echo -e "${YELLOW}📦 Provisioning new Neo4j container...${NC}"
        # Optimized memory for 32GB RAM system
        docker run -d \
            --name neo4j \
            --publish=$NEO4J_HTTP:7474 --publish=$NEO4J_BOLT:7687 \
            --volume "$NEO4J_DATA_DIR/data":/data \
            --volume "$NEO4J_DATA_DIR/plugins":/plugins \
            --env NEO4J_AUTH=neo4j/wikigraph \
            --env NEO4J_PLUGINS='["apoc", "graph-data-science"]' \
            --env NEO4J_dbms_security_procedures_unrestricted=gds.*,apoc.* \
            --env NEO4J_server_memory_heap_initial__size=4G \
            --env NEO4J_server_memory_heap_max__size=12G \
            --env NEO4J_server_memory_pagecache_size=8G \
            --env NEO4J_server_gds_memory_limit=6G \
            --env NEO4J_dbms_memory_transaction_total_max=8G \
            neo4j:5-community >/dev/null
    fi

    # Wait for Neo4j to be truly ready (not just port open)
    echo -n "   Waiting for Neo4j to accept queries..."
    local ready=0
    for i in {1..30}; do
        if docker exec neo4j cypher-shell -u neo4j -p wikigraph "RETURN 1" >/dev/null 2>&1; then
            ready=1
            break
        fi
        echo -n "."
        sleep 2
    done

    if [ $ready -eq 1 ]; then
        echo -e " ${GREEN}OK${NC}"
    else
        echo -e " ${RED}FAILED (Check docker logs neo4j)${NC}"
        return 1
    fi

    # 2. Start Backend API
    if is_port_open $BACKEND_PORT; then
        echo -e "${GREEN}✅ Backend API is already running.${NC}"
    else
        echo -e "${YELLOW}🧠 Starting FastAPI Backend...${NC}"
        cd "$PROJECT_ROOT"
        # Use setsid to detach process completely
        setsid python3 -m uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT < /dev/null > "$API_LOG" 2>&1 &
        echo $! > "$BACKEND_PID"
        wait_for_port $BACKEND_PORT "FastAPI"
    fi

    # 3. Start Frontend
    if is_port_open $FRONTEND_PORT; then
        echo -e "${GREEN}✅ Frontend is already running.${NC}"
    else
        echo -e "${YELLOW}🌌 Starting Next.js Frontend...${NC}"
        cd "$PROJECT_ROOT/frontend"
        # Using absolute paths for logs and PID prevents "No such file" errors
        nohup npm run dev -- -p $FRONTEND_PORT > "$FRONT_LOG" 2>&1 &
        echo $! > "$FRONTEND_PID"
        # Frontend takes a while, don't block
        sleep 2
    fi

    echo -e "${GREEN}==================================================${NC}"
    echo -e "${GREEN}✨ Environment Ready!${NC}"
    echo -e "🔗 Frontend: ${BLUE}http://localhost:$FRONTEND_PORT${NC}"
    echo -e "🔗 API Docs: ${BLUE}http://localhost:$BACKEND_PORT/docs${NC}"
    echo -e "🔗 Neo4j:    ${BLUE}http://localhost:$NEO4J_HTTP${NC}"
    echo -e "${GREEN}==================================================${NC}"
}

function stop() {
    echo -e "${RED}🛑 Stopping WikiGraph Lab...${NC}"
    
    # 1. Kill Processes by PID file
    for pid_file in "$FRONTEND_PID" "$BACKEND_PID"; do
        if [ -f "$pid_file" ]; then
            PID=$(cat "$pid_file")
            echo -n "   Stopping process $PID..."
            kill $PID 2>/dev/null || true
            rm "$pid_file"
            echo -e " ${GREEN}OK${NC}"
        fi
    done

    # 2. Aggressive Cleanup (pkill)
    echo -n "   Cleaning up lingering Node/Python processes..."
    pkill -f "next dev" 2>/dev/null || true
    pkill -f "uvicorn app.main:app" 2>/dev/null || true
    echo -e " ${GREEN}DONE${NC}"

    # 3. Wait for ports to clear
    echo -n "   Waiting for ports to release..."
    for i in {1..10}; do
        if ! is_port_open $FRONTEND_PORT && ! is_port_open $BACKEND_PORT; then
            echo -e " ${GREEN}OK${NC}"
            break
        fi
        echo -n "."
        sleep 1
        if [ $i -eq 10 ]; then
            echo -e " ${YELLOW}TIMEOUT (Forcing kill)${NC}"
            fuser -k $FRONTEND_PORT/tcp $BACKEND_PORT/tcp 2>/dev/null || true
        fi
    done

    echo -e "${GREEN}Local processes stopped.${NC}"
    echo -e "${YELLOW}Note: Neo4j container is left running. Run 'docker stop neo4j' to stop it.${NC}"
}

function status() {
    echo -e "${BLUE}📊 System Status:${NC}"
    
    # Neo4j Status
    if check_neo4j_container; then
        echo -e "Neo4j:    ${GREEN}RUNNING${NC}"
    elif [ $? -eq 2 ]; then
         echo -e "Neo4j:    ${YELLOW}STOPPED (Container Exists)${NC}"
    else
        echo -e "Neo4j:    ${RED}MISSING${NC}"
    fi

    # Backend Status
    if is_port_open $BACKEND_PORT; then
        echo -e "Backend:  ${GREEN}RUNNING${NC} (Port $BACKEND_PORT)"
    else
        echo -e "Backend:  ${RED}STOPPED${NC}"
    fi

    # Frontend Status
    if is_port_open $FRONTEND_PORT; then
        echo -e "Frontend: ${GREEN}RUNNING${NC} (Port $FRONTEND_PORT)"
    else
        echo -e "Frontend: ${RED}STOPPED${NC}"
    fi
}

function logs() {
    echo -e "${BLUE}📜 Tailing logs (Ctrl+C to exit)...${NC}"
    tail -f "$API_LOG" "$FRONT_LOG"
}

function clean() {
    echo -e "${RED}🧹 Cleaning up...${NC}"
    stop
    echo -n "Stopping and removing Neo4j container..."
    docker rm -f neo4j 2>/dev/null || true
    echo -e " ${GREEN}Done${NC}"
    echo -n "Removing log files..."
    rm -f "$API_LOG" "$FRONT_LOG" "$BACKEND_PID" "$FRONTEND_PID"
    echo -e " ${GREEN}Done${NC}"
}

function run_import() {
    echo -e "${RED}⚠️  WARNING: This will WIPE the current database and import from data/neo4j_bulk!${NC}"
    read -p "Are you sure? (y/N) " confirm
    if [[ "$confirm" != "y" ]]; then
        echo "Aborted."
        exit 0
    fi
    
    echo -e "${BLUE}📦 Starting Bulk Import...${NC}"
    # Delegate to the archive script for now, as it has the complex logic
    # Use absolute path to ensure we find it
    IMPORT_SCRIPT="$PROJECT_ROOT/archive/run_bulk_import.sh"
    if [ -f "$IMPORT_SCRIPT" ]; then
        cd "$PROJECT_ROOT"
        bash "$IMPORT_SCRIPT"
    else
        echo -e "${RED}❌ Import script not found at $IMPORT_SCRIPT${NC}"
    fi
}

# --- Dispatcher ---

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    status)
        status
        ;;
    restart)
        stop
        sleep 1
        start
        ;;
    logs)
        logs
        ;;
    clean)
        clean
        ;;
    import)
        run_import
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart|logs|clean|import}"
        exit 1
esac