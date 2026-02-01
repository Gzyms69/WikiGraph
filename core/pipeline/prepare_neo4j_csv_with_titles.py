#!/usr/bin/env python3
"""
TEST SCRIPT: prepare_neo4j_csv_with_titles.py
Modifies the original logic to include 'title' in nodes.csv.
"""

import sqlite3
import csv
import sys
from pathlib import Path
from tqdm import tqdm

def get_db_path(lang):
    return Path(f"data/db/{lang}.db")

def load_mappings(db_path):
    print("🧠 Loading metadata into memory...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Store (qid, title) tuple for source nodes
    id_map = {} # page_id -> (qid, title)
    
    print("   Loading Page ID -> QID map...")
    cursor.execute("""
        SELECT p.page_id, p.title, m.qid 
        FROM pages p 
        JOIN id_mapping m ON p.page_id = m.page_id
        WHERE p.namespace = 0
    """)
    
    for pid, title, qid in tqdm(cursor, desc="Loading Pages"):
        clean_title = title.replace(" ", "_")
        id_map[pid] = (qid, clean_title) # CHANGED: Store title
        
    conn.close()
    print(f"   Mapped {len(id_map)} article pages.")
    return id_map

def generate_csvs(lang, limit=None):
    db_path = get_db_path(lang)
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        sys.exit(1)
        
    id_map = load_mappings(db_path)
    
    out_dir = Path(f"data/neo4j_bulk_test/{lang}") # TEST DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    
    nodes_file = out_dir / "nodes.csv"
    
    # --- Step 1: Generate Nodes CSV ---
    print(f"📄 Generating {nodes_file.name}...")
    with open(nodes_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # CHANGED HEADER
        writer.writerow(["qid:ID", "title", "ns:int", ":LABEL"])
        
        count = 0
        for pid, (qid, title) in id_map.items():
            # CHANGED ROW
            writer.writerow([qid, title, 0, "Concept"])
            count += 1
            if limit and count >= limit: break
            
    print(f"✅ Generated {count} nodes with titles.")
    
    # Verify first few lines
    print("\n🔍 Verification (Head):")
    with open(nodes_file, 'r') as f:
        for _ in range(5):
            print(f.readline().strip())

if __name__ == "__main__":
    generate_csvs("pl", limit=100)
