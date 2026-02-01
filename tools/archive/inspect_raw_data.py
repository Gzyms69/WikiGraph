#!/bin/bash

echo "============================================================"
echo "RAW DATA SOURCE INVENTORY"
echo "============================================================"

echo -e "\n📁 RAW WIKIPEDIA DUMPS (Found in project):"
find data/ -name "*sql*" 2>/dev/null | head -20

echo -e "\n📁 DATA DIRECTORY STRUCTURE:"
ls -F data/
echo "--- data/neo4j_data ---"
ls -F data/neo4j_data/
echo "--- data/db ---"
ls -F data/db/

echo -e "\n📁 IMPORT SCRIPTS:"
find . -name "*import*" -o -name "*ingest*" -o -name "*loader*"
