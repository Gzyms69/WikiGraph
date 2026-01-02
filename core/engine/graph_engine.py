import csv
import sys
import time
import random
import logging
import functools
from pathlib import Path
from neo4j import GraphDatabase
from neo4j.exceptions import TransientError, ServiceUnavailable
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
import pandas as pd

# Global variable to hold the QID map, shared across worker processes via fork
qid_map_global = {}

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Top-level functions for multiprocessing (must be at module level to be picklable)
def execute_with_retry(driver, query, **kwargs):
    max_retries = 5
    for attempt in range(max_retries):
        try:
            with driver.session() as session:
                session.run(query, **kwargs)
            return
        except (TransientError, ServiceUnavailable):
            if attempt == max_retries - 1: raise
            time.sleep(0.5 * (2 ** attempt) + random.uniform(0, 0.5))

def get_qid_global(lang, page_id):
    """Get QID from the global map."""
    return qid_map_global.get(str(page_id), f"local:{lang}:{page_id}")

def process_concept_batch(batch_data, uri, user, password, max_connections):
    query = "UNWIND $batch AS qid MERGE (c:Concept {qid: qid})"
    driver = GraphDatabase.driver(
        uri,
        auth=(user, password),
        max_connection_lifetime=30*60,
        max_connection_pool_size=max_connections
    )
    try:
        execute_with_retry(driver, query, batch=batch_data)
    finally:
        driver.close()

def process_article_batch(batch_data, lang, uri, user, password, max_connections):
    query = """
    UNWIND $batch AS row
    MATCH (c:Concept {qid: row.qid})
    MERGE (a:Article {id: row.art_id})
    ON CREATE SET a.title = row.title, a.lang = $lang
    MERGE (a)-[:REPRESENTS]->(c)
    """
    driver = GraphDatabase.driver(
        uri,
        auth=(user, password),
        max_connection_lifetime=30*60,
        max_connection_pool_size=max_connections
    )
    try:
        execute_with_retry(driver, query, batch=batch_data, lang=lang)
    finally:
        driver.close()

def process_link_batch(batch_data, uri, user, password, max_connections):
    query = """
    UNWIND $batch AS row
    MATCH (sc:Concept {qid: row.s_qid})
    MERGE (tc:Concept {qid: row.t_qid})
    MERGE (sc)-[:LINKS_TO]->(tc)
    """
    driver = GraphDatabase.driver(
        uri,
        auth=(user, password),
        max_connection_lifetime=30*60,
        max_connection_pool_size=max_connections
    )
    try:
        execute_with_retry(driver, query, batch=batch_data)
    finally:
        driver.close()

class WikiGraphEngine:
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="wikigraph", max_connections=20):
        self.uri = uri
        self.auth = (user, password)
        self.max_connections = max_connections

    def _get_driver(self):
        return GraphDatabase.driver(
            self.uri,
            auth=self.auth,
            max_connection_lifetime=30*60,
            max_connection_pool_size=self.max_connections
        )

    def setup_constraints(self):
        """Ensure uniqueness before loading."""
        logging.info("🚀 Creating Neo4j constraints...")
        driver = self._get_driver()
        with driver.session() as session:
            session.run("CREATE CONSTRAINT concept_qid IF NOT EXISTS FOR (c:Concept) REQUIRE c.qid IS UNIQUE")
            session.run("CREATE CONSTRAINT article_id IF NOT EXISTS FOR (a:Article) REQUIRE a.id IS UNIQUE")
        driver.close()

    def load_resolver_to_memory(self, lang):
        """Ultra-fast QID mapping using pandas."""
        global qid_map_global  # Update the global variable
        csv_path = Path(f"data/processed/qids_{lang}.csv")
        logging.info(f"🧠 Loading {lang} QID mapping into memory...")
        df = pd.read_csv(csv_path)
        qid_map_global = dict(zip(df.iloc[:, 0].astype(str), df.iloc[:, 1]))
        logging.info(f"✅ Loaded {len(qid_map_global):,} mappings.")

    def _create_batches(self, tsv_path, batch_size, lang, mode='articles'):
        batches = []
        current_batch = []
        with open(tsv_path, 'r', encoding='utf-8') as f:
            if mode == 'articles':
                reader = csv.DictReader(f, delimiter='\t')
                for row in reader:
                    raw_id = row.get('id:ID(wiki)') or row.get('id:ID')
                    page_id = raw_id.split(':')[-1]
                    current_batch.append({
                        'qid': get_qid_global(lang, page_id),
                        'art_id': raw_id,
                        'title': row['title:STRING']
                    })
                    if len(current_batch) >= batch_size:
                        batches.append(current_batch)
                        current_batch = []
            elif mode == 'concepts':
                # Just extract unique QIDs from articles
                reader = csv.DictReader(f, delimiter='\t')
                unique_qids = set()
                for row in reader:
                    raw_id = row.get('id:ID(wiki)') or row.get('id:ID')
                    qid = get_qid_global(lang, raw_id.split(':')[-1])
                    unique_qids.add(qid)
                    if len(unique_qids) >= batch_size:
                        batches.append(list(unique_qids))
                        unique_qids = set()
                if unique_qids: batches.append(list(unique_qids))
                return batches
            else: # links
                reader = csv.reader(f, delimiter='\t')
                next(reader)
                for row in reader:
                    current_batch.append({
                        's_qid': get_qid_global(lang, row[0].split(':')[-1]),
                        't_qid': get_qid_global(lang, row[1].split(':')[-1])
                    })
                    if len(current_batch) >= batch_size:
                        batches.append(current_batch)
                        current_batch = []
        if current_batch: batches.append(current_batch)
        return batches

    def ingest_language(self, lang, articles_tsv, links_tsv, batch_size=5000, workers=4):
        # Load the QID map into the global variable before starting the process pool
        self.load_resolver_to_memory(lang)
        self.setup_constraints()

        # 1. Concepts (Pre-populate to avoid deadlocks)
        logging.info(f"💎 Phase 1: Pre-populating Concepts for {lang}...")
        batches = self._create_batches(articles_tsv, batch_size, lang, mode='concepts')
        
        # Use partial to bind non-varying arguments (picklable)
        func = functools.partial(process_concept_batch, uri=self.uri, user=self.auth[0], 
                                password=self.auth[1], max_connections=self.max_connections)
        
        with ProcessPoolExecutor(max_workers=workers) as executor:
            list(tqdm(executor.map(func, batches), total=len(batches), desc="Concepts"))

        # 2. Articles
        logging.info(f"📝 Phase 2: Ingesting Articles for {lang}...")
        batches = self._create_batches(articles_tsv, batch_size, lang, mode='articles')
        
        func = functools.partial(process_article_batch, lang=lang, uri=self.uri, user=self.auth[0], 
                                password=self.auth[1], max_connections=self.max_connections)
        
        with ProcessPoolExecutor(max_workers=workers) as executor:
            list(tqdm(executor.map(func, batches), total=len(batches), desc="Articles"))

        # 3. Links
        logging.info(f"🔗 Phase 3: Linking Concepts for {lang}...")
        batches = self._create_batches(links_tsv, batch_size, lang, mode='links')
        
        func = functools.partial(process_link_batch, uri=self.uri, user=self.auth[0], 
                                password=self.auth[1], max_connections=self.max_connections)
        
        with ProcessPoolExecutor(max_workers=workers) as executor:
            list(tqdm(executor.map(func, batches), total=len(batches), desc="Links"))

if __name__ == "__main__":
    engine = WikiGraphEngine()
    engine.ingest_language("pl",
                          "data/neo4j_import_clean/articles_clean.tsv",
                          "data/neo4j_import_clean/links_clean.tsv",
                          batch_size=5000,
                          workers=4)