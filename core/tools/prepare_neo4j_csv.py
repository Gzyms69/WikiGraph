#!/usr/bin/env python3
"""
Phase 2: Graph Topology Generator (Neo4j CSVs)
- Loads ID/Title mappings from SQLite into memory.
- Loads Link Targets (modern MediaWiki schema) from SQLite.
- Streams 'pagelinks' (from_id, from_ns, target_id) to generate 'edges.csv'.
- Generates 'nodes.csv' (QID, Namespace) from metadata.
- Applies strict Gates: Checksum & Row Counts.
"""

import sqlite3
import csv
import sys
import hashlib
from pathlib import Path
from mwsql import Dump
from tqdm import tqdm

def get_db_path(lang):
    return Path(f"data/db/{lang}.db")

def load_mappings(db_path):
    print("🧠 Loading metadata into memory...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    id_map = {} # page_id -> qid (for source nodes)
    title_map = {} # title -> qid (for target resolution, assume NS=0 for simplicity in graph core) 
    
    # Load Pages + QIDs
    # We filter for NS=0 (Articles) for the core graph to keep it clean, 
    # but source nodes can technically be others if we wanted. 
    # For now, let's strictly stick to Article -> Article graph.
    print("   Loading Page ID -> QID map...")
    cursor.execute("""
        SELECT p.page_id, p.title, m.qid 
        FROM pages p 
        JOIN id_mapping m ON p.page_id = m.page_id
        WHERE p.namespace = 0
    """,)
    
    for pid, title, qid in tqdm(cursor, desc="Loading Pages"):
        id_map[pid] = qid
        clean_title = title.replace(" ", "_")
        title_map[clean_title] = qid
        
    conn.close()
    print(f"   Mapped {len(id_map)} article pages.")
    return id_map, title_map

def load_link_targets(db_path):
    print("🎯 Loading Link Targets (Namespace 0 only)...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # We only care about targets that are Articles (NS=0)
    cursor.execute("SELECT lt_id, lt_title FROM link_targets WHERE lt_namespace = 0")
    
    target_map = {}
    for lt_id, lt_title in tqdm(cursor, desc="Loading Targets"):
        target_map[lt_id] = lt_title.replace(" ", "_")
        
    conn.close()
    print(f"   Mapped {len(target_map)} link targets.")
    return target_map

def generate_csvs(lang, limit=None):
    db_path = get_db_path(lang)
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        sys.exit(1)
        
    id_map, title_map = load_mappings(db_path)
    target_map = load_link_targets(db_path)
    
    out_dir = Path(f"data/neo4j_bulk/{lang}")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    nodes_file = out_dir / "nodes.csv"
    edges_file = out_dir / "edges.csv"
    
    # --- Step 1: Generate Nodes CSV ---
    print(f"📄 Generating {nodes_file.name}...")
    with open(nodes_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["qid:ID", "ns:int", ":LABEL"])
        
        # We assume all in id_map are NS 0 (Concept) based on the SQL query above
        for pid, qid in id_map.items():
            writer.writerow([qid, 0, "Concept"])
            
    # --- Step 2: Generate Edges CSV ---
    pl_dump = Path(f"data/raw/{lang}wiki-latest-pagelinks.sql.gz")
    if not pl_dump.exists():
        print(f"❌ Missing pagelinks dump: {pl_dump}")
        sys.exit(1)
        
    print(f"🔗 Generating {edges_file.name} from {pl_dump.name}...")
    if limit:
        print(f"⚠️  Running in LIMIT mode: Stopping after {limit:,} rows.")
    
    # pagelinks schema (1.39+): pl_from, pl_from_namespace, pl_target_id
    dump = Dump.from_file(str(pl_dump), encoding='latin1')
    
    edge_count = 0
    miss_count = 0
    skipped_ns = 0
    total_processed = 0
    
    with open(edges_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([":START_ID", ":END_ID", ":TYPE"])
        
        for row in tqdm(dump.rows(), desc="Processing Links", mininterval=1.0):
            if limit and total_processed >= limit:
                break
            
            total_processed += 1
            if len(row) < 3: continue
            
            try:
                src_id = int(row[0])
                # src_ns = int(row[1]) # We assume 0 based on id_map check
                target_id = int(row[2])
                
                # 1. Check Source (Must be a known Article)
                src_qid = id_map.get(src_id)
                if not src_qid:
                    continue 
                
                # 2. Resolve Target ID -> Title
                tgt_title = target_map.get(target_id)
                if not tgt_title:
                    # This means the target is not NS 0 (e.g., Talk, User, Category)
                    # or it's missing from our DB. We skip.
                    skipped_ns += 1
                    continue
                
                # 3. Resolve Title -> QID
                tgt_qid = title_map.get(tgt_title)
                
                if tgt_qid:
                    writer.writerow([src_qid, tgt_qid, "LINKS_TO"])
                    edge_count += 1
                else:
                    # Redlink or unmapped page
                    miss_count += 1
                    
            except (ValueError, IndexError): continue

    print(f"✅ Edges Created: {edge_count:,}")
    print(f"⚠️  Unresolved Targets (Redlinks): {miss_count:,}")
    print(f"ℹ️  Skipped Non-Article Targets: {skipped_ns:,}")
    print(f"📊 Total Rows Processed: {total_processed:,}")
    
    # --- Step 3: Checksums (Gate 3) ---
    print("\n🔐 Calculating Checksums...")
    for fpath in [nodes_file, edges_file]:
        h = hashlib.md5()
        with open(fpath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                h.update(chunk)
        print(f"   {fpath.name}: {h.hexdigest()}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", default="pl")
    parser.add_argument("--limit", type=int, default=None, help="Stop after N rows for testing")
    args = parser.parse_args()
    generate_csvs(args.lang, args.limit)
