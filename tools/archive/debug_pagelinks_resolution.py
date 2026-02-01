#!/usr/bin/env python3
"""
Validation Gate 3: Diagnostic for Pagelinks Resolution
- Samples 1 out of every 10,000 rows from pagelinks (Random/Uniform sampling).
- Simulates the full resolution pipeline: TargetID -> Title -> QID.
- Reports precise success/failure rates.
"""

import sqlite3
import sys
from pathlib import Path
from mwsql import Dump
from tqdm import tqdm

def get_db_path(lang):
    return Path(f"data/db/{lang}.db")

def load_mappings(db_path):
    print("🧠 Loading metadata...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    id_map = {}
    title_map = {}
    
    cursor.execute("""
        SELECT p.page_id, p.title, m.qid 
        FROM pages p 
        JOIN id_mapping m ON p.page_id = m.page_id
        WHERE p.namespace = 0
    """)
    for pid, title, qid in cursor:
        id_map[pid] = qid
        clean_title = title.replace(" ", "_")
        title_map[clean_title] = qid
    
    conn.close()
    print(f"   Mapped {len(id_map)} source pages.")
    return id_map, title_map

def load_link_targets(db_path):
    print("🎯 Loading Link Targets...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Loading ALL targets to debug NS mismatch, but map filtered for resolving
    cursor.execute("SELECT lt_id, lt_namespace, lt_title FROM link_targets")
    target_map = {}
    for lt_id, lt_ns, lt_title in cursor:
        target_map[lt_id] = (lt_ns, lt_title.replace(" ", "_"))
    conn.close()
    print(f"   Mapped {len(target_map)} targets (All Namespaces).")
    return target_map

def debug_resolution(lang="pl", sample_rate=10000):
    db_path = get_db_path(lang)
    id_map, title_map = load_mappings(db_path)
    target_map = load_link_targets(db_path)
    
    pl_dump = Path(f"data/raw/{lang}wiki-latest-pagelinks.sql.gz")
    dump = Dump.from_file(str(pl_dump), encoding='latin1')
    
    stats = {
        "total_scanned": 0,
        "sampled": 0,
        "src_missing": 0,
        "tgt_missing_in_db": 0,
        "tgt_ns_skipped": 0,
        "tgt_redlink": 0,
        "success": 0
    }
    
    print(f"\n🔍 Sampling 1 out of every {sample_rate} links...")
    
    for row in dump.rows():
        stats["total_scanned"] += 1
        if stats["total_scanned"] % sample_rate != 0:
            continue
            
        if len(row) < 3: continue
        stats["sampled"] += 1
        
        try:
            src_id = int(row[0])
            target_id = int(row[2])
            
            # 1. Source Check
            if src_id not in id_map:
                stats["src_missing"] += 1
                continue
                
            # 2. Target ID Check
            tgt_info = target_map.get(target_id)
            if not tgt_info:
                stats["tgt_missing_in_db"] += 1
                continue
            
            tgt_ns, tgt_title = tgt_info
            
            if tgt_ns != 0:
                stats["tgt_ns_skipped"] += 1
                continue
                
            # 3. Title Check
            if tgt_title in title_map:
                stats["success"] += 1
            else:
                stats["tgt_redlink"] += 1
                
        except Exception:
            continue

    print("\n=== VALIDATION GATE 3 REPORT ===")
    print(f"Total Scanned: {stats['total_scanned']}")
    print(f"Total Sampled: {stats['sampled']}")
    
    valid_src = stats['sampled'] - stats['src_missing']
    if stats['sampled'] > 0:
        print(f"Valid Source Nodes: {valid_src} ({(valid_src/stats['sampled'])*100:.1f}%)")
    
    if valid_src > 0:
        print(f"Detailed Breakdown (of {valid_src} valid sources):")
        print(f"✅ SUCCESS (Edge Created): {stats['success']} ({(stats['success']/valid_src)*100:.1f}%)")
        print(f"⏭️  Target Skipped (NS!=0): {stats['tgt_ns_skipped']} ({(stats['tgt_ns_skipped']/valid_src)*100:.1f}%)")
        print(f"❌ Target Redlink:         {stats['tgt_redlink']} ({(stats['tgt_redlink']/valid_src)*100:.1f}%)")
        print(f"❌ Target Missing in DB:   {stats['tgt_missing_in_db']} ({(stats['tgt_missing_in_db']/valid_src)*100:.1f}%)")
        
        success_rate = stats['success'] / valid_src
        # Adjusted success rate: (Success) / (Success + Redlinks)
        # We exclude NS skipped because we INTEND to skip them.
        relevant_targets = stats['success'] + stats['tgt_redlink']
        if relevant_targets > 0:
            adj_success = stats['success'] / relevant_targets
            print(f"Adjusted Success Rate (Articles Only): {adj_success*100:.1f}%")
        
        print("-" * 30)
        if success_rate > 0.5:
            print("✅ GATE PASSED (>50% Overall Success)")
        elif (stats['success'] + stats['tgt_ns_skipped']) / valid_src > 0.9:
             print("✅ GATE PASSED (High Data Integrity, many non-article links)")
        else:
            print("⚠️ GATE WARNING")

if __name__ == "__main__":
    debug_resolution()