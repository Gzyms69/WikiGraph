#!/bin/bash

# WikiGraph Development Control Script (Multi-Container)
# Usage: ./dev.sh [start|stop|status] [pl|de|all]

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
# Safe Memory Settings (Total ~8GB per container)
HEAP="4G"
PAGECACHE="4G"

function start_container() {
    local lang=$1
    local http_port=$2
    local bolt_port=$3
    local container_name="neo4j-$lang"
    local data_dir="$PROJECT_ROOT/data/neo4j_data/$lang"

    echo -e "${BLUE}🚀 Starting $lang ($container_name)...${NC}"
    
    # Check existence
    if docker ps -a --format '{{.Names}}' | grep -q "^$container_name$"; then
        if docker ps --format '{{.Names}}' | grep -q "^$container_name$"; then
            echo -e "${GREEN}✅ $container_name is already running.${NC}"
            return
        else
            echo -e "${YELLOW}📦 Starting existing container...${NC}"
            docker start $container_name >/dev/null
        fi
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

    # Health Check
    echo -n "   Waiting for $container_name..."
    for i in {1..30}; do
        if docker exec $container_name cypher-shell -u neo4j -p wikigraph "RETURN 1" >/dev/null 2>&1; then
            echo -e " ${GREEN}OK${NC}"
            return
        fi
        echo -n "."
        sleep 2
    done
    echo -e " ${RED}TIMEOUT${NC}"
}

function stop_container() {
    local lang=$1
    local container_name="neo4j-$lang"
    echo -n "🛑 Stopping $container_name..."
    docker stop $container_name >/dev/null 2>&1
    echo -e " ${GREEN}DONE${NC}"
}

# --- Command Router ---

CMD=$1
TARGET=${2:-pl} # Default to Polish if not specified

case "$CMD" in
    start)
        if [[ "$TARGET" == "pl" || "$TARGET" == "all" ]]; then
            start_container "pl" 7474 7687
        fi
        if [[ "$TARGET" == "de" || "$TARGET" == "all" ]]; then
            start_container "de" 7475 7688
        fi
        ;;
    stop)
        if [[ "$TARGET" == "pl" || "$TARGET" == "all" ]]; then
            stop_container "pl"
        fi
        if [[ "$TARGET" == "de" || "$TARGET" == "all" ]]; then
            stop_container "de"
        fi
        ;;
    status)
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep neo4j
        ;;    
    *)
        echo "Usage: ./dev.sh {start|stop|status} {pl|de|all}"
        exit 1
        ;;
esac
