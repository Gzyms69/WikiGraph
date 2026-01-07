#!/bin/bash
set -e

CONCEPT_FILES=""
ARTICLE_FILES=""
EDGE_FILES=""

# Find all languages in the bulk directory
LANGS=$(ls -1 data/neo4j_bulk/)

if [ -z "$LANGS" ]; then
    echo "❌ No bulk data found in data/neo4j_bulk/. Run exporter first."
    exit 1
fi

echo "🔍 Found datasets for: $(echo $LANGS | xargs)"

for lang in $LANGS; do
    CONCEPT_FILES="$CONCEPT_FILES --nodes=Concept=\"/import/$lang/nodes_concepts.csv\""
    ARTICLE_FILES="$ARTICLE_FILES --nodes=Article=\"/import/$lang/nodes_articles.csv\""
    EDGE_FILES="$EDGE_FILES --relationships=REPRESENTS=\"/import/$lang/edges_represents.csv\""
    EDGE_FILES="$EDGE_FILES --relationships=LINKS_TO=\"/import/$lang/edges_links.csv\""
done

# 2. Stop Neo4j
echo "🛑 Stopping Neo4j..."
docker rm -f neo4j || true

# 3. Clean Data Store
echo "🧹 Wiping existing database..."
rm -rf data/neo4j_data/data
mkdir -p data/neo4j_data/data

# 4. Run Unified Import
echo "🚀 Running multi-language neo4j-admin import..."

# We mount the parent 'data/neo4j_bulk' to '/import'
docker run --interactive --tty --rm \
    --volume "$(pwd)/data/neo4j_bulk":/import \
    --volume "$(pwd)/data/neo4j_data/data":/data \
    neo4j:5-community \
    bash -c "neo4j-admin database import full \
        $CONCEPT_FILES \
        $ARTICLE_FILES \
        $EDGE_FILES \
        --overwrite-destination \
        --skip-duplicate-nodes=true \
        --bad-tolerance=10000000 \
        --verbose \
        neo4j"

# 5. Start Neo4j
echo "🟢 Starting Neo4j Server..."
docker run -d \
    --name neo4j \
    --publish=7474:7474 --publish=7687:7687 \
    --volume "$(pwd)/data/neo4j_data/data":/data \
    --env NEO4J_AUTH=neo4j/wikigraph \
    --env NEO4J_server_memory_heap_initial__size=4G \
    --env NEO4J_server_memory_heap_max__size=8G \
    --env NEO4J_server_memory_pagecache_size=8G \
    neo4j:5-community

echo "✅ Unified Import Complete!"