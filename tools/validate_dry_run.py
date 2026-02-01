import sqlite3
import json
import random
from pathlib import Path

def validate_dry_run():
    db_path = Path('data/db/de.db')
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.execute('''
        SELECT title, infobox FROM pages 
        WHERE infobox IS NOT NULL 
        ORDER BY RANDOM() LIMIT 100
    ''')
    
    rows = cursor.fetchall()
    if not rows:
        print("❌ No infoboxes found in database!")
        return

    issues = 0
    checked = 0
    for title, ib in rows:
        checked += 1
        try:
            data = json.loads(ib)
            if not isinstance(data, list):
                issues += 1
                print(f"❌ {title}: Infobox not a list")
                continue
            
            if len(data) == 0:
                issues += 1
                print(f"❌ {title}: Empty infobox list")
                continue
                
            # Basic validation of structure
            for item in data:
                if 'template' not in item or 'params' not in item:
                    issues += 1
                    print(f"❌ {title}: Missing template/params keys")
                    break
                
                # Check for German infobox prefix
                if not any(item['template'].startswith(p) for p in ['Infobox']):
                    # Sometimes templates are used without 'Infobox' prefix but are matched?
                    # No, our script strictly matches prefix.
                    # Wait, if prefix is 'Infobox', then template must start with 'Infobox'.
                    pass

        except Exception as e:
            issues += 1
            print(f"❌ {title}: JSON error: {e}")

    print(f"\nChecked {checked} random articles.")
    if issues == 0:
        print("✅ PASS: Data integrity looks solid.")
    else:
        print(f"❌ FAIL: {issues} issues found.")
    
    # Check total count
    cursor = conn.execute("SELECT COUNT(*) FROM pages WHERE infobox IS NOT NULL")
    count = cursor.fetchone()[0]
    print(f"Total articles with infoboxes in DB: {count}")
    
    conn.close()

if __name__ == "__main__":
    validate_dry_run()
