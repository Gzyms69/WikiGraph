#!/bin/bash
# Core Neo4j Bulk Import Script (Multi-Language)
# Usage: ./core/tools/run_neo4j_import.sh [pl|de]

LANG=${1:-pl}
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DATA_DIR="$PROJECT_ROOT/data/neo4j_data/$LANG"
BULK_DIR="$PROJECT_ROOT/data/neo4j_bulk/$LANG"
CONTAINER_NAME="neo4j-$LANG"

echo -e "\033[0;34m📦 WikiGraph Bulk Importer ($LANG)\033[0m"

# Validation
if [ ! -f "$BULK_DIR/nodes.csv" ]; then
    echo -e "\033[0;31m❌ Missing CSV files in $BULK_DIR\033[0m"
    exit 1
fi

# 1. Stop Neo4j Container
echo -n "   Stopping $CONTAINER_NAME container..."
docker stop $CONTAINER_NAME >/dev/null 2>&1
# We do NOT remove the container here if we want to preserve settings, 
# BUT for a fresh import, we usually want a clean slate.
# Since dev.sh handles provisioning, removing it ensures we get a clean mount.
docker rm $CONTAINER_NAME >/dev/null 2>&1
echo -e "\033[0;32m DONE\033[0m"

# 2. Clear Data Directory
echo -n "   Clearing old graph data in $DATA_DIR..."
# Use docker to remove root-owned files
docker run --rm -v "$DATA_DIR":/data alpine sh -c 'rm -rf /data/data /data/logs'
mkdir -p "$DATA_DIR/data" "$DATA_DIR/logs" "$DATA_DIR/plugins"
echo -e "\033[0;32m DONE\033[0m"

# 3. Run Import
echo -e "   Running neo4j-admin import..."
# We use a temporary import container to do the job
docker run --rm \
    --volume "$DATA_DIR/data":/data \
    --volume "$BULK_DIR":/import \
    neo4j:5-community \
    neo4j-admin database import full \
    --nodes=/import/nodes.csv \
    --relationships=/import/edges.csv \
    --overwrite-destination \
    --verbose

if [ $? -eq 0 ]; then
    echo -e "\033[0;32m✅ Import Successful.\033[0m"
else
    echo -e "\033[0;31m❌ Import Failed.\033[0m"
    exit 1
fi

# 4. Restart Container (via dev.sh)
echo -e "\033[0;33m🚀 Restarting $CONTAINER_NAME...\033[0m"
"$PROJECT_ROOT/dev.sh" start $LANG