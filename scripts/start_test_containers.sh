#!/bin/bash
set -e

# WikiGraph Test Container Launcher
# Starts ISOLATED Neo4j instances on test ports (7476/7477)
# by creating a SNAPSHOT COPY of production data.

mkdir -p logs/test_containers

start_test_container() {
    local lang=$1
    local name="neo4j-$lang-test"
    local http_port=$2
    local bolt_port=$3
    # Production Data Source
    local prod_data="$(pwd)/data/neo4j_data/$lang/data"
    # Test Data Destination
    local test_dir="$(pwd)/data/neo4j_test/$lang"
    local test_data="$test_dir/data"

    echo "🚀 Provisioning $name (Test Mode)..."
    echo "   Source: $prod_data"
    echo "   Dest:   $test_data (SNAPSHOT)"

    # Cleanup old container
    docker rm -f $name >/dev/null 2>&1 || true

    # Create Snapshot (Copy Data)
    echo -n "   Creating snapshot (may take ~30s)..."
    mkdir -p "$test_dir"
    # Use rsync for efficiency (only copy changed files if re-running)
    # Exclude lock files just in case
    rsync -a --delete --exclude 'store_lock' "$prod_data/" "$test_data/"
    echo " DONE"
    
    # Start Container (RW on Snapshot)
    # We use standard RW mount because it's a copy.
    
    docker run -d \
        --name $name \
        -p $http_port:7474 \
        -p $bolt_port:7687 \
        -v "$test_data":/data \
        -v "$(pwd)/logs/test_containers/$lang":/logs \
        -e NEO4J_AUTH=neo4j/wikigraph \
        -e NEO4J_server_memory_heap_initial__size=1G \
        -e NEO4J_server_memory_heap_max__size=1G \
        neo4j:5-community >/dev/null

    # Wait for readiness
    echo -n "   Waiting for readiness..."
    for i in {1..60}; do
        if docker exec $name cypher-shell -u neo4j -p wikigraph "RETURN 1" >/dev/null 2>&1; then
            echo " OK"
            return
        fi
        echo -n "."
        sleep 2
    done
    echo " FAIL (Timeout)"
    docker logs $name | tail -n 5
    return 1
}

# Start PL and DE test containers
start_test_container "pl" 7476 7689
start_test_container "de" 7477 7690

echo "✅ Test Infrastructure Ready."
