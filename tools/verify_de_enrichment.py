import sqlite3
import json
from collections import Counter

conn = sqlite3.connect('data/db/de.db')

def verify_new_templates():
    print("🔍 Verifying presence of Taxobox and Personendaten in DB...")
    cursor = conn.execute("SELECT infobox FROM pages WHERE infobox IS NOT NULL")
    
    stats = Counter()
    
    for (ib_json,) in cursor:
        try:
            data = json.loads(ib_json)
            if not data: continue
            
            for tmpl in data:
                name = tmpl.get('template', '').strip()
                if name == 'Taxobox':
                    stats['Taxobox'] += 1
                elif name == 'Personendaten':
                    stats['Personendaten'] += 1
                elif name.startswith('Infobox'):
                    stats['Infobox'] += 1
        except:
            pass

    print("\n📊 Template Counts:")
    for k, v in stats.most_common():
        print(f"  - {k}: {v}")

    if stats['Taxobox'] > 0 or stats['Personendaten'] > 0:
        print("\n✅ SUCCESS: New templates are being extracted.")
    else:
        print("\n❌ FAILURE: New templates NOT found.")

if __name__ == "__main__":
    verify_new_templates()

