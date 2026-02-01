import sqlite3
import json
from collections import Counter

conn = sqlite3.connect('data/db/pl.db')

def analyze_patterns():
    print("\n=== 4. POLISH PATTERN DISTRIBUTION (PYTHON) ===")
    cursor = conn.execute("SELECT infobox FROM pages WHERE infobox IS NOT NULL")
    
    stats = Counter()
    total = 0
    
    for (ib_json,) in cursor:
        total += 1
        try:
            data = json.loads(ib_json)
            if not data:
                stats['empty_list'] += 1
                continue
                
            tmpl = data[0].get('template', '').strip()
            
            if tmpl.startswith('Infobox') or tmpl.startswith('Infokarta'):
                stats['prefix_only'] += 1
            elif tmpl.lower().endswith('infobox'):
                stats['suffix_only'] += 1
            elif 'infobox' in tmpl.lower():
                stats['mixed_or_other'] += 1
            else:
                stats['unknown'] += 1
        except:
            stats['json_error'] += 1

    for key, count in stats.most_common():
        pct = (count / total) * 100
        print(f"{key}: {count} ({pct:.2f}%)")

def sample_inspection():
    print("\n=== 5. RANDOM SAMPLE INSPECTION ===")
    cursor = conn.execute("SELECT title, infobox FROM pages WHERE infobox IS NOT NULL ORDER BY RANDOM() LIMIT 10")
    
    for title, ib in cursor:
        try:
            data = json.loads(ib)
            tmpl = data[0]['template'] if data else 'EMPTY'
            print(f"\nTitle: {title}")
            print(f"  Template: {tmpl}")
            params = data[0].get('params', {}).keys() if data else []
            print(f"  Params: {list(params)[:3]}...")
        except Exception as e:
            print(f"  Error: {e}")

analyze_patterns()
sample_inspection()
