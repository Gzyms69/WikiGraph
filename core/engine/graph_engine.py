import csv
import sys
import time
import random
import logging
import functools
import gzip
import json
from pathlib import Path
from neo4j import GraphDatabase
from neo4j.exceptions import TransientError, ServiceUnavailable
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
import pandas as pd

# Global variables shared across worker processes via fork
qid_map_global = {}
title_qid_map_global = {}

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
    # FAST QID-to-QID LINKING
    query = """
    UNWIND $batch AS row
    MATCH (sc:Concept {qid: row.sqid})
    MATCH (tc:Concept {qid: row.tqid})
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
        """Ensure uniqueness and indexing before loading."""
        logging.info("🚀 Creating Neo4j constraints...")
        driver = self._get_driver()
        with driver.session() as session:
            session.run("CREATE CONSTRAINT concept_qid IF NOT EXISTS FOR (c:Concept) REQUIRE c.qid IS UNIQUE")
            session.run("CREATE CONSTRAINT article_id IF NOT EXISTS FOR (a:Article) REQUIRE a.id IS UNIQUE")
        driver.close()

    def load_resolver_to_memory(self, lang):
        """Ultra-fast QID mapping using pandas."""
        global qid_map_global
        csv_path = Path(f"data/processed/qids_{lang}.csv")
        logging.info(f"🧠 Loading {lang} QID mapping into memory...")
        df = pd.read_csv(csv_path)
        qid_map_global = dict(zip(df.iloc[:, 0].astype(str), df.iloc[:, 1]))
        logging.info(f"✅ Loaded {len(qid_map_global):,} mappings.")

    def build_title_qid_map(self, lang, data_dir):
        """Builds a Title -> QID map in memory for fast link resolution."""
        global title_qid_map_global
        logging.info(f"📚 Building Title -> QID map for {lang}...")
        data_path = Path(data_dir)
        article_files = sorted(list(data_path.glob("articles_batch_*.jsonl.gz")))
        
        count = 0
        for f in article_files:
            with gzip.open(f, 'rt', encoding='utf-8') as fin:
                for line in fin:
                    data = json.loads(line)
                    qid = get_qid_global(lang, data['id'])
                    title_qid_map_global[data['title']] = qid
                    count += 1
        logging.info(f"✅ Map built with {count:,} titles.")

    def _create_batches(self, file_path, batch_size, lang, mode='articles'):
        batches = []
        current_batch = []
        path = Path(file_path)
        
        if mode in ['articles', 'concepts']:
            with gzip.open(path, 'rt', encoding='utf-8') as f:
                for line in f:
                    data = json.loads(line)
                    page_id = str(data['id'])
                    if mode == 'articles':
                        current_batch.append({
                            'qid': get_qid_global(lang, page_id),
                            'art_id': f"{lang}:{page_id}",
                            'title': data['title']
                        })
                    else: # concepts
                        current_batch.append(get_qid_global(lang, page_id))

                    if len(current_batch) >= batch_size:
                        batches.append(list(set(current_batch)) if mode == 'concepts' else current_batch)
                        current_batch = []
                        
        elif mode == 'links':
            # Resolve Titles to QIDs locally to offload Neo4j
            with gzip.open(path, 'rt', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    # row = [SourceTitle, TargetTitle, Lang]
                    sqid = title_qid_map_global.get(row[0])
                    tqid = title_qid_map_global.get(row[1])
                    
                    if sqid and tqid:
                        current_batch.append({'sqid': sqid, 'tqid': tqid})
                    
                    if len(current_batch) >= batch_size:
                        batches.append(current_batch)
                        current_batch = []

        if current_batch:
            batches.append(list(set(current_batch)) if mode == 'concepts' else current_batch)
        return batches

    def ingest_language(self, lang, data_dir, batch_size=5000, workers=4):
        self.load_resolver_to_memory(lang)
        self.build_title_qid_map(lang, data_dir)
        self.setup_constraints()
        
        data_path = Path(data_dir)
        article_files = sorted(list(data_path.glob("articles_batch_*.jsonl.gz")))
        link_files = sorted(list(data_path.glob("links_batch_*.csv.gz")))

        # 1. Concepts
        logging.info(f"💎 Phase 1: Pre-populating Concepts for {lang}...")
        func = functools.partial(process_concept_batch, uri=self.uri, user=self.auth[0], 
                                password=self.auth[1], max_connections=self.max_connections)
        for f in article_files:
            batches = self._create_batches(f, batch_size, lang, mode='concepts')
            with ProcessPoolExecutor(max_workers=workers) as executor:
                list(tqdm(executor.map(func, batches), total=len(batches), desc=f"Concepts ({f.name})"))

        # 2. Articles
        logging.info(f"📝 Phase 2: Ingesting Articles for {lang}...")
        func = functools.partial(process_article_batch, lang=lang, uri=self.uri, user=self.auth[0], 
                                password=self.auth[1], max_connections=self.max_connections)
        for f in article_files:
            batches = self._create_batches(f, batch_size, lang, mode='articles')
            with ProcessPoolExecutor(max_workers=workers) as executor:
                list(tqdm(executor.map(func, batches), total=len(batches), desc=f"Articles ({f.name})"))

        # 3. Links
        logging.info(f"🔗 Phase 3: Linking Concepts for {lang}...")
        func = functools.partial(process_link_batch, uri=self.uri, user=self.auth[0], 
                                password=self.auth[1], max_connections=self.max_connections)
        for f in link_files:
            batches = self._create_batches(f, batch_size, lang, mode='links')
            with ProcessPoolExecutor(max_workers=workers) as executor:
                list(tqdm(executor.map(func, batches), total=len(batches), desc=f"Links ({f.name})"))