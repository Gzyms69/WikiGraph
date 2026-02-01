import sqlite3
import json
import time
import random
import textwrap
from collections import Counter

DB_DE = 'data/db/de.db'
DB_PL = 'data/db/pl.db'

def run_tests():
    print("🚀 STARTING COMPREHENSIVE VALIDATION...\n")
    conn = sqlite3.connect(DB_DE)
    
    # --- TEST 2: Parameter Extraction Quality ---
    print("🔹 TEST 2: Parameter Quality (1000 samples)")
    cursor = conn.execute('SELECT infobox FROM pages WHERE infobox IS NOT NULL ORDER BY RANDOM() LIMIT 1000')
    empty_params = 0
    total_templates = 0
    for (ib_json,) in cursor:
        try:
            data = json.loads(ib_json)
            for tmpl in data:
                total_templates += 1
                if not tmpl.get('params'):
                    empty_params += 1
        except: pass
    
    pct_valid = (total_templates - empty_params) * 100 / total_templates if total_templates else 0
    print(f"   Templates checked: {total_templates}")
    print(f"   Empty params: {empty_params}")
    print(f"   ✅ Richness: {pct_valid:.1f}% have parameters (Target: >90%)")

    # --- TEST 1: Suspicious Templates ---
    print("\n🔹 TEST 1: Suspicious Patterns (50k scan)")
    cursor = conn.execute('SELECT infobox FROM pages WHERE infobox IS NOT NULL LIMIT 50000')
    suspicious = []
    for (ib_json,) in cursor:
        try:
            data = json.loads(ib_json)
            for tmpl in data:
                name = tmpl.get('template', '')
                if '{{' in name or '}}' in name or '|' in name or len(name) > 100:
                    suspicious.append(name)
        except: pass
    print(f"   Suspicious templates: {len(suspicious)}")
    if suspicious:
        print("   Top suspicious:", Counter(suspicious).most_common(5))

    # --- TEST 6: Multiple Templates ---
    print("\n🔹 TEST 6: Multiple Template Analysis")
    cursor = conn.execute('SELECT infobox FROM pages WHERE infobox IS NOT NULL')
    template_counts = []
    for (ib_json,) in cursor:
        try:
            data = json.loads(ib_json)
            template_counts.append(len(data))
        except: pass
    
    multi = sum(1 for c in template_counts if c > 1)
    print(f"   Total articles: {len(template_counts):,}")
    print(f"   Multi-template articles: {multi:,} ({multi*100/len(template_counts):.1f}%)")
    print(f"   Max templates in one article: {max(template_counts) if template_counts else 0}")

    # --- TEST 5: Performance Benchmark ---
    print("\n🔹 TEST 5: SQLite Performance")
    cursor = conn.execute('SELECT qid FROM id_mapping ORDER BY RANDOM() LIMIT 1')
    test_qid = cursor.fetchone()[0]
    
    start = time.time()
    for _ in range(100):
        conn.execute('SELECT p.title, p.infobox FROM pages p JOIN id_mapping m ON p.page_id = m.page_id WHERE m.qid = ?', (test_qid,))
    qid_time = (time.time() - start) * 10
    print(f"   Query by QID: {qid_time:.2f}ms")

    conn.close()

    # --- TEST 4: Cross-Language Comparison ---
    print("\n🔹 TEST 4: Cross-Language Richness (DE vs PL)")
    conn_de = sqlite3.connect(DB_DE)
    conn_pl = sqlite3.connect(DB_PL)
    
    # Get overlapping
    qids_de = set(row[0] for row in conn_de.execute("SELECT m.qid FROM id_mapping m JOIN pages p ON m.page_id=p.page_id WHERE p.infobox IS NOT NULL LIMIT 2000"))
    qids_pl = set(row[0] for row in conn_pl.execute("SELECT m.qid FROM id_mapping m JOIN pages p ON m.page_id=p.page_id WHERE p.infobox IS NOT NULL LIMIT 2000"))
    overlap = list(qids_de & qids_pl)
    
    print(f"   Overlapping sample pool: {len(overlap)}")
    
    # Safe sample logic: handle cases where overlap is smaller than 10
    sample_size = min(10, len(overlap))
    sample = random.sample(overlap, sample_size) if sample_size > 0 else []
    
    print(f"   {'QID':<10} | {'DE Params':<10} | {'PL Params':<10} | Title")
    print("-" * 60)
    
    for qid in sample:
        de_row = conn_de.execute("SELECT p.infobox, p.title FROM pages p JOIN id_mapping m ON p.page_id=m.page_id WHERE m.qid=?", (qid,)).fetchone()
        pl_row = conn_pl.execute("SELECT p.infobox FROM pages p JOIN id_mapping m ON p.page_id=m.page_id WHERE m.qid=?", (qid,)).fetchone()
        
        de_params = sum(len(t.get('params', {})) for t in json.loads(de_row[0]))
        pl_params = sum(len(t.get('params', {})) for t in json.loads(pl_row[0]))
        print(f"   {qid:<10} | {de_params:<10} | {pl_params:<10} | {de_row[1][:30]}")

    conn_de.close()
    conn_pl.close()

if __name__ == "__main__":
    run_tests()
