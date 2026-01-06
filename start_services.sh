#!/bin/bash
set -e

echo "🚀 Starting WikiGraph Services (Neo4j + GDS + APOC)..."

# Stop existing container
docker rm -f neo4j || true

# Start Neo4j with Plugins
# We use NEO4J_PLUGINS env var to auto-install APOC and GDS
docker run -d \
    --name neo4j \
    --publish=7474:7474 --publish=7687:7687 \
    --volume "$(pwd)/data/neo4j_data/data":/data \
    --volume "$(pwd)/data/neo4j_data/plugins":/plugins \
    --env NEO4J_AUTH=neo4j/wikigraph \
    --env NEO4J_PLUGINS='["apoc", "graph-data-science"]' \
    --env NEO4J_dbms_security_procedures_unrestricted=gds.*,apoc.* \
    --env NEO4J_server_memory_heap_initial__size=4G \
    --env NEO4J_server_memory_heap_max__size=8G \
    --env NEO4J_server_memory_pagecache_size=8G \
    neo4j:5-community

echo "✅ Neo4j is starting."
echo "   - Plugins: APOC, Graph Data Science"
echo "   - Monitor: docker logs -f neo4j"
