#!/usr/bin/env python3
"""
CORE: REDIRECT LOADER
Loads Wikipedia alias nodes (Redirects) into Neo4j from CSV.
"""

import csv
import argparse
from pathlib import Path
from neo4j import GraphDatabase
from tqdm import tqdm

def load_redirects(uri, user, password, csv_path, lang):
    print(f"Connecting to Neo4j to load redirects for [{lang}]...")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    if not csv_path.exists():
        print(f"❌ ERROR: Redirect file not found: {csv_path}")
        return

    # 1. Create Constraint for Alias
    with driver.session() as session:
        session.run("CREATE CONSTRAINT alias_title_unique IF NOT EXISTS FOR (a:Alias) REQUIRE (a.title, a.lang) IS UNIQUE")

    # 2. Upload in batches
    def upload_batch(batch):
        query = """
        UNWIND $batch AS row
        MERGE (a:Alias {title: row.alias, lang: $lang})
        WITH a, row
        MATCH (target:Article {title: row.target, lang: $lang})
        CREATE (a)-[:REDIRECTS_TO]->(target)
        """
        with driver.session() as session:
            session.run(query, batch=batch, lang=lang)

    batch = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in tqdm(reader, desc="Importing Redirects"):
            if len(row) < 2: continue
            batch.append({'alias': row[0], 'target': row[1]})
            if len(batch) >= 5000:
                upload_batch(batch)
                batch = []
    
    if batch:
        upload_batch(batch)

    driver.close()
    print("✓ Redirect import complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--lang', default='pl')
    args = parser.parse_args()

    base_dir = Path(__file__).parent.parent
    csv_path = base_dir / 'data' / 'processed' / args.lang / 'redirects_verified.csv'
    
    load_redirects("bolt://localhost:7687", "neo4j", "wikigraph", csv_path, args.lang)