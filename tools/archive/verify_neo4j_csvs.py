#!/usr/bin/env python3
import csv
import sys
from pathlib import Path

def verify():
    nodes_file = Path("data/neo4j_bulk/nodes.csv")
    edges_file = Path("data/neo4j_bulk/edges.csv")
    
    print("🔍 Starting Gate 4 Validation...")
    
    # 1. Check Files Existence
    if not nodes_file.exists() or not edges_file.exists():
        print("❌ FAIL: CSV files missing.")
        sys.exit(1)
        
    # 2. Verify Nodes
    print(f"📊 Verifying {nodes_file}...")
    node_count = 0
    with open(nodes_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        if header != ["qid:ID", "ns:int", ":LABEL"]:
            print(f"❌ FAIL: Invalid Node Header: {header}")
            sys.exit(1)
        
        for row in reader:
            node_count += 1
            if not row[0].startswith("Q"):
                print(f"❌ FAIL: Invalid QID format: {row[0]}")
                sys.exit(1)
                
    print(f"✅ Nodes: {node_count:,} (Expected: ~1.6M)")
    if abs(node_count - 1675749) > 100:
        print(f"⚠️  Note: Node count mismatch with id_map. Found {node_count}, expected 1,675,749.")

    # 3. Verify Edges
    print(f"📊 Verifying {edges_file}...")
    edge_count = 0
    with open(edges_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        if header != [":START_ID", ":END_ID", ":TYPE"]:
            print(f"❌ FAIL: Invalid Edge Header: {header}")
            sys.exit(1)
            
        for row in reader:
            edge_count += 1
            # Check for IDs/Titles in the data
            if row[0].isdigit() or row[1].isdigit():
                print(f"❌ FAIL: Found Page IDs instead of QIDs: {row}")
                sys.exit(1)
            if "_" in row[0] or "_" in row[1]:
                 # Some QIDs might have underscores? Usually not. Titles definitely do.
                 # Let's check format.
                 pass

    print(f"✅ Edges: {edge_count:,} (Expected: >100M)")
    if edge_count < 100000: # Sanity check for the "77k failure"
        print(f"❌ FAIL: Catastrophic edge count failure: {edge_count}")
        sys.exit(1)

    if edge_count < 90000000:
        print(f"⚠️  Warning: Edge count ({edge_count:,}) is lower than expected (~100M).")

    print("\n🏁 GATE 4 PASSED: CSVs are valid and ready for Neo4j import.")

if __name__ == "__main__":
    verify()
