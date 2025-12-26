#!/usr/bin/env python3
"""
CORE: NEO4J LOADER
High Performance Neo4j Loader with ID resolution in Python and parallel Bolt sessions.
"""

import argparse
import gzip
import json
import csv
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from neo4j import GraphDatabase
    from tqdm import tqdm
except ImportError:
    print("Please install requirements: pip install neo4j tqdm")
    sys.exit(1)

class Neo4jLoader:
    def __init__(self, uri, user, password, lang):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.lang = lang
        self.title_to_id = {}

    def close(self):
        self.driver.close()

    def create_constraints(self):
        print("Creating constraints...")
        with self.driver.session() as session:
            session.run(f"CREATE CONSTRAINT article_id_unique IF NOT EXISTS FOR (a:Article) REQUIRE (a.id, a.lang) IS UNIQUE")
            session.run(f"CREATE INDEX article_title_index IF NOT EXISTS FOR (a:Article) ON (a.title, a.lang)")

    def build_title_map(self, data_dir: Path):
        print("Building title -> ID mapping in RAM...")
        files = sorted(data_dir.glob('articles_batch_*.jsonl.gz'))
        for fpath in tqdm(files, desc="Parsing Articles"):
            with gzip.open(fpath, 'rt', encoding='utf-8') as f:
                for line in f:
                    article = json.loads(line)
                    self.title_to_id[article['title']] = article['id']
        print(f"✓ Map built: {len(self.title_to_id):,} entries")

    def load_articles(self, data_dir: Path):
        print("Loading Articles into Neo4j...")
        files = sorted(data_dir.glob('articles_batch_*.jsonl.gz'))
        
        def upload_batch(batch):
            with self.driver.session() as session:
                session.run("""
                    UNWIND $batch AS row
                    MERGE (a:Article {id: row.id, lang: $lang})
                    SET a.title = row.title
                """, batch=batch, lang=self.lang)

        for fpath in tqdm(files, desc="Uploading Articles"):
            batch = []
            with gzip.open(fpath, 'rt', encoding='utf-8') as f:
                for line in f:
                    a = json.loads(line)
                    batch.append({'id': a['id'], 'title': a['title']})
                    if len(batch) >= 5000:
                        upload_batch(batch)
                        batch = []
                if batch: upload_batch(batch)

    def load_links_parallel(self, data_dir: Path):
        print("Loading Links into Neo4j (Parallel)...")
        files = sorted(data_dir.glob('links_batch_*.csv.gz'))
        query = """
            UNWIND $batch AS row
            MATCH (s:Article {id: row.sid, lang: $lang})
            MATCH (t:Article {id: row.tid, lang: $lang})
            CREATE (s)-[:LINKS_TO]->(t)
        """

        def process_file(fpath):
            batch, count = [], 0
            with gzip.open(fpath, 'rt', encoding='utf-8', newline='') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) < 2: continue
                    sid, tid = self.title_to_id.get(row[0]), self.title_to_id.get(row[1])
                    if sid and tid:
                        batch.append({'sid': sid, 'tid': tid})
                        if len(batch) >= 2500:
                            with self.driver.session() as session: session.run(query, batch=batch, lang=self.lang)
                            count += len(batch); batch = []
                if batch:
                    with self.driver.session() as session: session.run(query, batch=batch, lang=self.lang)
                    count += len(batch)
            return count

        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(tqdm(executor.map(process_file, files), total=len(files), desc="Processing Links"))
        print(f"✓ Total links created: {sum(results):,}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--lang', default='pl')
    args = parser.parse_args()

    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / 'data' / 'processed' / args.lang
    
    loader = Neo4jLoader("bolt://localhost:7687", "neo4j", "wikigraph", args.lang)
    try:
        loader.create_constraints()
        loader.build_title_map(data_dir)
        loader.load_articles(data_dir) 
        loader.load_links_parallel(data_dir)
    finally: loader.close()

if __name__ == "__main__":
    main()
