import asyncio
import logging
import sys
import os
import json
from tabulate import tabulate

# Add project root to path
sys.path.append(os.getcwd())

from app.core.config import settings
from app.services.neo4j_manager import Neo4jManager
from app.services.metadata_manager import MetadataManager

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("DeepDive")

async def investigate_earth_topology(neo4j: Neo4jManager, meta: MetadataManager):
    print("\n--- [Q2] EARTH TOPOLOGY INVESTIGATION ---")
    langs = ['pl', 'de', 'es']
    results = []
    
    for lang in langs:
        # Check incoming vs outgoing
        in_query = "MATCH (n:Concept {qid: 'Q2'})<-[r]-() RETURN count(r) as count"
        out_query = "MATCH (n:Concept {qid: 'Q2'})-[r]->() RETURN count(r) as count"
        
        in_res = await neo4j.query(lang, in_query)
        out_res = await neo4j.query(lang, out_query)
        
        in_count = in_res[0]['count'] if in_res else 0
        out_count = out_res[0]['count'] if out_res else 0
        
        # Sample incoming connections in PL if count is huge
        sample_titles = []
        if lang == 'pl' and in_count > 10000:
            sample_query = "MATCH (n:Concept {qid: 'Q2'})<-[]-(m) RETURN m.qid as qid LIMIT 5"
            samples = await neo4j.query(lang, sample_query)
            for s in samples:
                title = meta.get_title(lang, s['qid'])
                sample_titles.append(title)
        
        results.append([lang.upper(), in_count, out_count, ", ".join(sample_titles[:3])])

    print(tabulate(results, headers=["Lang", "Incoming", "Outgoing", "Samples (Incoming)"], tablefmt="grid"))

async def investigate_german_metadata_gap(meta: MetadataManager):
    print("\n--- [DE] GERMAN METADATA GAP INVESTIGATION ---")
    # Rosetta Stone QIDs where DE had 0 complexity but others had > 0
    test_qids = [
        {"qid": "Q64", "label": "Berlin"},
        {"qid": "Q362", "label": "World War II"},
        {"qid": "Q2736", "label": "Football"},
    ]
    
    results = []
    for entry in test_qids:
        qid = entry['qid']
        label = entry['label']
        
        pl_ib = meta.get_infobox('pl', qid)
        de_ib = meta.get_infobox('de', qid)
        es_ib = meta.get_infobox('es', qid)
        
        def format_ib(ib):
            if ib is None: return "MISSING (None)"
            if not ib: return "EMPTY ([])"
            # Return list of template names found
            return ", ".join([t.get('template', 'Unknown') for t in ib])

        results.append([
            f"{label} ({qid})",
            format_ib(pl_ib),
            format_ib(de_ib),
            format_ib(es_ib)
        ])
    
    print(tabulate(results, headers=["Concept", "PL Templates", "DE Templates", "ES Templates"], tablefmt="grid"))

    # Forensic: Why is DE Berlin (Q64) empty?
    # Check title first
    de_title = meta.get_title('de', 'Q64')
    print(f"\nForensic DE Berlin (Q64): Title = '{de_title}'")
    
    # Check raw infobox column for a sample article in DE that SHOULD have one
    # Use Berlin as it's the most obvious
    import sqlite3
    db_path = "data/db/de.db"
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cursor = conn.cursor()
        cursor.execute("SELECT p.infobox FROM pages p JOIN id_mapping m ON p.page_id = m.page_id WHERE m.qid = 'Q64'")
        row = cursor.fetchone()
        conn.close()
        print(f"Raw SQLite Infobox for Q64 (DE): {row[0] if row else 'NOT FOUND'}")
    except Exception as e:
        print(f"SQLite Error: {e}")

async def main():
    neo4j = Neo4jManager()
    meta = MetadataManager()
    
    await investigate_earth_topology(neo4j, meta)
    await investigate_german_metadata_gap(meta)
    
    neo4j.close()

if __name__ == "__main__":
    asyncio.run(main())
