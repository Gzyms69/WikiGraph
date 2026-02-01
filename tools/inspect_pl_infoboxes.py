import sqlite3
import json
import random

DB_PATH = 'data/db/pl.db'

def inspect():
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    
    # Get total count
    count = conn.execute("SELECT COUNT(*) FROM pages WHERE infobox IS NOT NULL").fetchone()[0]
    print(f"📦 Total Polish Infoboxes: {count}")

    # Fetch 5 random samples
    print("\n🔍 Random Samples:")
    rows = conn.execute("SELECT title, infobox FROM pages WHERE infobox IS NOT NULL ORDER BY RANDOM() LIMIT 5").fetchall()
    
    for title, ib_json in rows:
        print(f"\n--- {title} ---")
        try:
            data = json.loads(ib_json)
            # Print first template details
            if data:
                tmpl = data[0]
                print(f"Template Name: {tmpl['template']}")
                print("Parameters (First 3):")
                for k, v in list(tmpl['params'].items())[:3]:
                    print(f"  - {k}: {v[:50]}...") # Truncate long values
            else:
                print("⚠️ Empty list")
        except Exception as e:
            print(f"❌ JSON Error: {e}")

    # Explicitly check for a Suffix Pattern
    print("\n🔍 Checking for specific Suffix Pattern 'Władca infobox'...")
    rows = conn.execute("SELECT title, infobox FROM pages WHERE infobox LIKE '%Władca infobox%' LIMIT 1").fetchall()
    if rows:
        print(f"✅ Found example: {rows[0][0]}")
        print(json.dumps(json.loads(rows[0][1]), indent=2, ensure_ascii=False))
    else:
        print("⚠️ No 'Władca infobox' found in current sample.")

inspect()
