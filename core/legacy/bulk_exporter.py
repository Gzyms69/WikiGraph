#!/usr/bin/env python3
"""
CORE: BULK EXPORTER
High-performance converter from Processed JSONL -> Neo4j Bulk Import CSVs.
"""

import csv
import gzip
import json
import logging
import sys
from pathlib import Path
from tqdm import tqdm

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# Global Maps
qid_map_global = {}          # PageID -> QID
title_qid_map_global = {}    # Title -> QID

def load_qid_map(lang):
    """Loads QID map (PageID -> QID) into memory."""
    global qid_map_global
    csv_path = Path(f"data/processed/qids_{lang}.csv")
    logging.info(f"🧠 Loading {lang} QID map...")
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        next(reader) # Skip header
        qid_map_global = {row[0]: row[1] for row in reader}
    logging.info(f"✅ Loaded {len(qid_map_global):,} QIDs.")

def build_title_map(article_files, lang):
    """
    Pass 1: Build Title -> QID map from all article batches.
    """
    global title_qid_map_global
    logging.info(f"📚 Building Title -> QID map for {lang}...")
    
    count = 0
    for f in tqdm(article_files, desc="Building Title Map"):
        with gzip.open(f, 'rt', encoding='utf-8') as fin:
            for line in fin:
                try:
                    data = json.loads(line)
                    page_id = str(data['id'])
                    # Resolve QID using the PageID map
                    qid = qid_map_global.get(page_id, f"local:{lang}:{page_id}")
                    
                    # Store Title -> QID
                    title_qid_map_global[data['title']] = qid
                    count += 1
                except json.JSONDecodeError:
                    continue
    logging.info(f"✅ Map built with {count:,} titles.")

def process_files(lang, data_dir, output_dir):
    """
    Main processing logic:
    1. Write Concepts & Articles (reading JSONL again)
    2. Write Links (reading CSVs and resolving via map)
    """
    
    # Prepare Output Files
    f_concepts = open(output_dir / "nodes_concepts.csv", 'w', newline='', encoding='utf-8')
    f_articles = open(output_dir / "nodes_articles.csv", 'w', newline='', encoding='utf-8')
    f_edges_rep = open(output_dir / "edges_represents.csv", 'w', newline='', encoding='utf-8')
    f_edges_links = open(output_dir / "edges_links.csv", 'w', newline='', encoding='utf-8')
    
    # CSV Writers
    w_concepts = csv.writer(f_concepts)
    w_concepts.writerow(['qid:ID'])
    
    w_articles = csv.writer(f_articles)
    w_articles.writerow([':ID', 'title', 'lang'])
    
    w_edges_rep = csv.writer(f_edges_rep)
    w_edges_rep.writerow([':START_ID', ':END_ID', ':TYPE'])

    w_edges_links = csv.writer(f_edges_links)
    w_edges_links.writerow([':START_ID', ':END_ID', ':TYPE'])
    
    # Get Files
    article_files = sorted(list(data_dir.glob("articles_batch_*.jsonl.gz")))
    link_files = sorted(list(data_dir.glob("links_batch_*.csv.gz")))

    # --- PASS 1: NODES (Articles & Concepts) ---
    logging.info("📝 Exporting Nodes (Concepts & Articles)...")
    seen_concepts = set()
    
    for f in tqdm(article_files, desc="Exporting Nodes"):
        with gzip.open(f, 'rt', encoding='utf-8') as fin:
            for line in fin:
                try:
                    data = json.loads(line)
                    page_id = str(data['id'])
                    qid = qid_map_global.get(page_id, f"local:{lang}:{page_id}")
                    
                    # Write Concept (Unique)
                    if qid not in seen_concepts:
                        w_concepts.writerow([qid])
                        seen_concepts.add(qid)
                    
                    # Write Article
                    article_uuid = f"{lang}:{page_id}"
                    w_articles.writerow([article_uuid, data['title'], lang])
                    
                    # Write Edge: Article -> Concept
                    w_edges_rep.writerow([article_uuid, qid, "REPRESENTS"])
                    
                except json.JSONDecodeError:
                    continue

    # --- PASS 2: EDGES (Links) ---
    logging.info("🔗 Exporting Links (Resolving Targets)...")
    link_count = 0
    resolved_count = 0
    
    for f in tqdm(link_files, desc="Exporting Links"):
        with gzip.open(f, 'rt', encoding='utf-8') as fin:
            reader = csv.reader(fin)
            # Row format: Source Title, Target Title, Lang
            for row in reader:
                s_title = row[0]
                t_title = row[1]
                
                s_qid = title_qid_map_global.get(s_title)
                t_qid = title_qid_map_global.get(t_title)
                
                link_count += 1
                
                if s_qid and t_qid:
                    # Write Edge: Concept -> Concept
                    w_edges_links.writerow([s_qid, t_qid, "LINKS_TO"])
                    resolved_count += 1

    logging.info(f"📊 Links Processed: {link_count:,}")
    logging.info(f"✅ Links Resolved:  {resolved_count:,} ({resolved_count/link_count*100:.1f}%)")

    f_concepts.close()
    f_articles.close()
    f_edges_rep.close()
    f_edges_links.close()

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 core/bulk_exporter.py <lang>")
        sys.exit(1)
        
    lang = sys.argv[1]
    data_dir = Path(f"data/processed/{lang}")
    output_dir = Path(f"data/neo4j_bulk/{lang}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Load PageID->QID Map
    load_qid_map(lang)
    
    # 2. Build Title->QID Map (Pass 1)
    # We re-scan the article files. Since they are compressed, reading them twice 
    # is actually safer/easier than keeping 2GB of objects in memory if we just want the map.
    article_files = sorted(list(data_dir.glob("articles_batch_*.jsonl.gz")))
    build_title_map(article_files, lang)
    
    # 3. Process & Export (Pass 2)
    process_files(lang, data_dir, output_dir)
    
    logging.info("✅ Bulk Export Complete.")
    logging.info(f"📂 Output: {output_dir}")

if __name__ == "__main__":
    main()
