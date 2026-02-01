import sqlite3
import time
import os
import sys
import re
from pathlib import Path
from app.services.neo4j_manager import Neo4jManager
import asyncio

# Ensure we can import from app
sys.path.append(os.getcwd())

async def check_infrastructure():
    print("\n--- Infrastructure Check ---")
    
    # Check SQLite files
    for lang in ['pl', 'de']:
        path = Path(f"data/db/{lang}.db")
        status = "Present" if path.exists() else "Missing"
        size = f"{path.stat().st_size / (1024*1024):.2f} MB" if path.exists() else "N/A"
        print(f"SQLite {lang.upper()}: {status} ({size})")

    # Check Neo4j Connectivity
    manager = Neo4jManager()
    health = manager.check_health()
    for lang, status in health.items():
        print(f"Neo4j {lang.upper()}: {'Running' if status['connected'] else 'Stopped'} (Latency: {status.get('latency_ms', 'N/A')}ms)")
    
    return manager

def check_sqlite(lang):
    print(f"\n--- SQLite Audit ({lang.upper()}) ---")
    db_path = f"data/db/{lang}.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    results = {}

    # 1. Schema Verification
    cur.execute("PRAGMA table_info(pages)")
    columns = {row[1]: row[2] for row in cur.fetchall()}
    results['columns'] = columns
    
    print(f"Columns in 'pages': {list(columns.keys())}")
    
    required = {'out_degree': 'INTEGER', 'in_degree': 'INTEGER', 'infobox': 'JSON'} # JSON is usually TEXT or BLOB in sqlite depending on creation, checking key existence primarily
    for col, type_hint in required.items():
        if col in columns:
            print(f"✅ Column '{col}' exists (Type: {columns[col]})")
        else:
            print(f"❌ Column '{col}' MISSING")

    # 2. Data Sampling
    print("\nSampling 5 Canonical Articles:")
    cur.execute("""
        SELECT page_id, title, out_degree, in_degree, infobox 
        FROM pages 
        WHERE namespace=0 AND is_redirect=0 AND out_degree > 0
        LIMIT 5
    """)
    rows = cur.fetchall()
    for row in rows:
        print(f"  ID: {row[0]}, Title: {row[1]}, Out: {row[2]}, In: {row[3]}, Infobox: {row[4]}")
        if row[4] is not None:
            print(f"  ⚠️ Infobox is NOT NULL (Expected NULL for now)")

    # 3. Counts
    cur.execute("SELECT COUNT(*) FROM pages WHERE namespace=0 AND is_redirect=0")
    canonical_count = cur.fetchone()[0]
    results['canonical_count'] = canonical_count
    
    cur.execute("SELECT COUNT(*) FROM pages WHERE namespace=0 AND is_redirect=1")
    redirect_count = cur.fetchone()[0]
    
    print(f"\nCanonical Articles (NS=0, No-Redir): {canonical_count:,}")
    print(f"Redirects (NS=0): {redirect_count:,}")
    
    conn.close()
    return results

async def check_neo4j(manager, lang, sqlite_count):
    print(f"\n--- Neo4j Audit ({lang.upper()}) ---")
    
    # 1. Node Count
    query_count = "MATCH (n:Concept) RETURN count(n) as total"
    res = await manager.query(lang, query_count)
    neo4j_count = res[0]['total']
    
    print(f"Neo4j Node Count: {neo4j_count:,}")
    print(f"SQLite Canonical: {sqlite_count:,}")
    
    if neo4j_count == sqlite_count:
        print("✅ Counts Match Exactly")
    else:
        diff = neo4j_count - sqlite_count
        print(f"❌ Mismatch: {diff:+,} nodes")

    # 2. Property Cleanup Verification
    query_props = """
    MATCH (n:Concept)
    WHERE n.title IS NOT NULL OR n.out_degree IS NOT NULL OR n.in_degree IS NOT NULL
    RETURN count(n) as dirty
    """
    res = await manager.query(lang, query_props)
    dirty_count = res[0]['dirty']
    
    if dirty_count == 0:
        print("✅ Properties Clean (No title/degrees found)")
    else:
        print(f"❌ {dirty_count} nodes still have forbidden properties")

    # 3. Redirect Contamination Check (Sample)
    # Pick 10 random nodes and check if they are redirects in SQLite
    query_sample = "MATCH (n:Concept) RETURN n.qid LIMIT 10"
    res = await manager.query(lang, query_sample)
    sample_qids = [r['n.qid'] for r in res]
    
    conn = sqlite3.connect(f"data/db/{lang}.db")
    cur = conn.cursor()
    
    print("\nRedirect Contamination Check (Sample 10):")
    clean_sample = True
    for qid in sample_qids:
        cur.execute("""
            SELECT p.is_redirect, p.title 
            FROM pages p 
            JOIN id_mapping m ON p.page_id = m.page_id 
            WHERE m.qid = ?
        """, (qid,))
        row = cur.fetchone()
        if row:
            is_redirect = row[0]
            if is_redirect:
                print(f"❌ Found Redirect in Neo4j: {qid} ({row[1]})")
                clean_sample = False
        else:
            print(f"⚠️ Node {qid} not found in SQLite id_mapping")
    
    if clean_sample:
        print("✅ Sample clean (No redirects found)")
    
    conn.close()

def check_tools():
    print("\n--- Toolchain Code Audit ---")
    
    # 1. sqlite_loader.py
    with open("core/sqlite_loader.py", "r") as f:
        content = f.read()
        if "infobox JSON" in content:
            print("✅ core/sqlite_loader.py: 'infobox JSON' found in SCHEMA")
        else:
            print("❌ core/sqlite_loader.py: 'infobox JSON' MISSING in SCHEMA")

    # 2. prepare_neo4j_csv.py
    with open("core/tools/prepare_neo4j_csv.py", "r") as f:
        content = f.read()
        if "WHERE p.namespace = 0 AND p.is_redirect = 0" in content:
            print("✅ core/tools/prepare_neo4j_csv.py: Redirect filter FOUND")
        else:
            print("❌ core/tools/prepare_neo4j_csv.py: Redirect filter MISSING")

async def main():
    start_time = time.time()
    manager = await check_infrastructure()
    
    check_tools()
    
    for lang in ['pl', 'de']:
        sqlite_res = check_sqlite(lang)
        await check_neo4j(manager, lang, sqlite_res['canonical_count'])
        
    print(f"\nAudit completed in {time.time() - start_time:.2f}s")
    manager.close()

if __name__ == "__main__":
    asyncio.run(main())
