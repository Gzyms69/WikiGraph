import sqlite3
import json
import random
from pathlib import Path
import argparse

def validate_full_extraction():
    parser = argparse.ArgumentParser()
    parser.add_argument('--lang', default='de', help='Language code')
    parser.add_argument('--samples', type=int, default=1000, help='Number of random samples to check')
    args = parser.parse_args()

    db_path = Path(f'data/db/{args.lang}.db')
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    
    # 1. Count Sanity Check
    cursor = conn.execute("SELECT COUNT(*) FROM pages WHERE infobox IS NOT NULL")
    total_count = cursor.fetchone()[0]
    print(f"🔬 Found {total_count:,} articles with infoboxes.")
    
    # 2. JSON Integrity and Pattern Validation
    cursor = conn.execute(f'''
        SELECT title, infobox FROM pages 
        WHERE infobox IS NOT NULL 
        ORDER BY RANDOM() LIMIT {args.samples}
    ''')
    
    rows = cursor.fetchall()
    if not rows:
        print("❌ No infoboxes found in database!")
        return

    json_issues = 0
    pattern_issues = 0
    checked_count = 0

    print(f"\n🔬 Checking {len(rows)} random samples for integrity...")
    for title, ib in rows:
        checked_count += 1
        try:
            data = json.loads(ib)
            if not isinstance(data, list) or not data:
                json_issues += 1
                print(f"  - ❌ {title}: Infobox is not a valid, non-empty list.")
                continue

            # Check if at least one template starts with "Infobox"
            if not any(isinstance(item, dict) and item.get('template', '').startswith('Infobox') for item in data):
                pattern_issues += 1
                print(f"  - ⚠️  {title}: No template found starting with 'Infobox'. First template: {data[0].get('template', 'N/A')}")
        except Exception as e:
            json_issues += 1
            print(f"  - ❌ {title}: JSON error: {e}")

    print(f"\n--- Validation Summary ---")
    print(f"Total samples checked: {checked_count}")
    
    if json_issues == 0:
        print("✅ JSON Integrity: PASS (All samples are valid JSON lists)")
    else:
        print(f"❌ JSON Integrity: FAIL ({json_issues} issues)")

    if pattern_issues == 0:
        print("✅ Pattern Validation: PASS (All samples match 'Infobox%' pattern)")
    else:
        print(f"❌ Pattern Validation: FAIL ({pattern_issues} issues)")
        
    if json_issues == 0 and pattern_issues == 0:
        print("\n🎉 Overall Validation: SUCCESS")
    else:
        print("\n🔥 Overall Validation: FAILED")

    conn.close()

if __name__ == "__main__":
    validate_full_extraction()
