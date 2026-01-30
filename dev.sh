#!/bin/bash

# WikiGraph Development Control Script
# Usage: ./dev.sh [start|stop|restart|status]

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# --- Configuration ---
HEAP="4G"
PAGECACHE="4G"
BACKEND_PORT=8000
BACKEND_LOG="$LOG_DIR/backend.log"

function start_container() {
    local lang=$1
    local http_port=$2
    local bolt_port=$3
    local container_name="neo4j-$lang"
    local data_dir="$PROJECT_ROOT/data/neo4j_data/$lang"

    echo -e "${BLUE}🚀 Starting Neo4j ($lang)...${NC}"
    
    if docker ps --format '{{.Names}}' | grep -q "^$container_name$"; then
        echo -e "${GREEN}✅ $container_name is already running.${NC}"
    elif docker ps -a --format '{{.Names}}' | grep -q "^$container_name$"; then
        echo -e "${YELLOW}📦 Starting existing container...${NC}"
        docker start $container_name >/dev/null
    else
        echo -e "${YELLOW}📦 Provisioning new container...${NC}"
        docker run -d \
            --name $container_name \
            --publish=$http_port:7474 --publish=$bolt_port:7687 \
            --volume "$data_dir/data":/data \
            --volume "$data_dir/plugins":/plugins \
            --env NEO4J_AUTH=neo4j/wikigraph \
            --env NEO4J_PLUGINS='["apoc", "graph-data-science"]' \
            --env NEO4J_dbms_security_procedures_unrestricted=gds.*,apoc.* \
            --env NEO4J_server_memory_heap_initial__size=2G \
            --env NEO4J_server_memory_heap_max__size=$HEAP \
            --env NEO4J_server_memory_pagecache_size=$PAGECACHE \
            neo4j:5-community >/dev/null
    fi
}

function wait_for_neo4j() {
    local lang=$1
    local container_name="neo4j-$lang"
    echo -n "   Waiting for $container_name to be ready..."
    
    for i in {1..30}; do
        if docker exec $container_name cypher-shell -u neo4j -p wikigraph "RETURN 1" >/dev/null 2>&1; then
            echo -e " ${GREEN}OK${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
    done
    echo -e " ${RED}TIMEOUT${NC}"
    return 1
}

function start_backend() {
    echo -e "${BLUE}🚀 Starting Backend (FastAPI)...${NC}"
    if pgrep -f "uvicorn app.main:app" > /dev/null; then
        echo -e "${GREEN}✅ Backend is already running (PID: $(pgrep -f "uvicorn app.main:app")).${NC}"
    else
        nohup "$PROJECT_ROOT/venv_gate5/bin/uvicorn" app.main:app --host 0.0.0.0 --port $BACKEND_PORT > "$BACKEND_LOG" 2>&1 &
        local pid=$!
        echo -e "${GREEN}✅ Backend started (PID: $pid). Logs: $BACKEND_LOG${NC}"
    fi
}

function stop_all() {
    echo -e "${RED}🛑 Stopping Environment...${NC}"
    
    if pgrep -f "uvicorn app.main:app" > /dev/null; then
        pkill -f "uvicorn app.main:app"
        echo -e "   Backend stopped."
    else
        echo -e "   Backend not running."
    fi

    for lang in pl de; do
        container="neo4j-$lang"
        if docker ps -q -f name=$container > /dev/null; then
            docker stop $container > /dev/null
            echo -e "   $container stopped."
        fi
    done
}

function check_status() {
    echo -e "\n${BLUE}=== System Status ===${NC}"
    
    echo -e "${YELLOW}Neo4j Containers:${NC}"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep neo4j || echo "   (None running)"
    
    echo -e "\n${YELLOW}Backend:${NC}"
    if pgrep -f "uvicorn app.main:app" > /dev/null; then
        pid=$(pgrep -f "uvicorn app.main:app")
        echo -e "   Running (PID: $pid, Port: $BACKEND_PORT)"
        echo -e "   Health Check:"
        # Wait a moment for backend to initialize connections
        sleep 2
        curl -s "http://localhost:$BACKEND_PORT/api/health" | head -c 200
        echo "..."
    else
        echo -e "   STOPPED"
    fi
    echo ""
}

CMD=$1

case "$CMD" in
    start)
        start_container "pl" 7474 7687
        start_container "de" 7475 7688
        
        wait_for_neo4j "pl" 
        wait_for_neo4j "de" 
        
        start_backend
        check_status
        ;;
    stop)
        stop_all
        ;;
    restart)
        stop_all
        sleep 2
        $0 start
        ;;
    status)
        check_status
        ;;    
    *)
        echo "Usage: ./dev.sh {start|stop|restart|status}"
        exit 1
        ;; 
esac
