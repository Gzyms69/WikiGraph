#!/usr/bin/env python3
"""
Gate Verification Script (Phase 1)
Checks row counts and encoding integrity for Polish DB.
"""

import sqlite3
import argparse
from pathlib import Path

def verify(lang):
    db_path = Path(f"data/db/{lang}.db")
    if not db_path.exists():
        print(f"❌ Database {db_path} not found!")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print(f"📊 --- Gate 1: Row Counts [{lang.upper()}] ---")
    
    # Official stats (approx): PL ~1.6M
    EXPECTED_PL = 1600000
    THRESHOLD = 0.05 # 5% variance allowed for "approx" 
    
    try:
        count = cursor.execute("SELECT COUNT(*) FROM pages WHERE namespace = 0").fetchone()[0]
        print(f"   Pages (NS=0): {count:,}")
        
        if lang == 'pl':
            if abs(count - EXPECTED_PL) / EXPECTED_PL < THRESHOLD:
                print("   ✅ Gate 1 PASSED: Count within expected range.")
            else:
                print(f"   ❌ Gate 1 FAILED: Count {count} differs significantly from expected {EXPECTED_PL}.")
    except Exception as e:
        print(f"   ❌ Gate 1 ERROR: {e}")

    print("\n🔍 --- Gate 2: Data Integrity (Encoding) ---")
    rows = cursor.execute("""
        SELECT p.title, cl.category_name 
        FROM category_links cl
        JOIN pages p ON cl.page_id = p.page_id
        WHERE p.namespace = 0
        LIMIT 10
    """).fetchall()
    
    for r in rows:
        print(f"   Article: {r[0]} -> Cat: {r[1]}")
    
    print("\n   [Manual Check Required]: Do the above look like valid Polish text?")
    print("   Good: 'Polska', 'Język', 'Historia'")
    print("   Bad: 'JÃªzyk', 'Historia_Å›wiata'")

    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", default="pl")
    args = parser.parse_args()
    verify(args.lang)