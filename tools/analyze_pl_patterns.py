import mwxml
import mwparserfromhell
import bz2
import json
import re
from pathlib import Path
from collections import Counter

# Configuration
DUMP_PATH = 'data/raw/plwiki-20251201-pages-articles-multistream.xml.bz2'
LIMIT = 10000

def analyze_patterns():
    print(f"🔬 Starting Polish Pattern Analysis on first {LIMIT} articles...")
    
    stats = {
        'processed': 0,
        'prefix_match': 0,
        'suffix_match': 0,
        'no_infobox': 0,
        'prefix_examples': Counter(),
        'suffix_examples': Counter()
    }

    # Regex for fast pre-check (Suffix pattern)
    # Looking for 'infobox}}' or 'infobox|' or 'infobox\n'
    suffix_re = re.compile(r'infobox', re.IGNORECASE)

    try:
        with bz2.open(DUMP_PATH, 'rt', encoding='utf-8', errors='ignore') as f:
            dump = mwxml.Dump.from_file(f)
            
            for page in dump:
                if page.namespace != 0:
                    continue
                
                # Check for redirects (heuristic: usually short and contain #REDIRECT)
                # mwxml doesn't strictly parse redirects in the header, we check content later or rely on revision length/content
                
                for revision in page:
                    text = revision.text or ""
                    
                    # Basic Redirect Filter
                    if text.upper().startswith("#REDIRECT") or text.upper().startswith("#PATRZ"):
                        continue

                    stats['processed'] += 1
                    
                    # Parse
                    wikicode = mwparserfromhell.parse(text)
                    templates = wikicode.filter_templates()
                    
                    has_prefix = False
                    has_suffix = False
                    
                    found_templates = []

                    for t in templates:
                        name = str(t.name).strip()
                        lower_name = name.lower()
                        
                        # 1. Check Prefix (Current Logic)
                        if name.startswith("Infobox") or name.startswith("Infokarta"):
                            has_prefix = True
                            stats['prefix_examples'][name] += 1
                            found_templates.append(f"PREFIX: {name}")
                        
                        # 2. Check Suffix (Missed Logic)
                        elif lower_name.endswith("infobox"):
                            has_suffix = True
                            stats['suffix_examples'][name] += 1
                            found_templates.append(f"SUFFIX: {name}")

                    if has_prefix:
                        stats['prefix_match'] += 1
                    elif has_suffix:
                        stats['suffix_match'] += 1
                        # print(f"  ⚠️ Missed Suffix Pattern in '{page.title}': Found {found_templates}")
                    else:
                        stats['no_infobox'] += 1

                    if stats['processed'] % 1000 == 0:
                        print(f"   ... processed {stats['processed']} articles. Prefix: {stats['prefix_match']} | Suffix (Missed): {stats['suffix_match']}")

                    if stats['processed'] >= LIMIT:
                        break
                
                if stats['processed'] >= LIMIT:
                    break

    except FileNotFoundError:
        print(f"❌ Dump file not found: {DUMP_PATH}")
        return

    print("\n" + "="*50)
    print("📊 ANALYSIS RESULTS (Polish Wikipedia)")
    print("="*50)
    print(f"Total Canonical Articles Checked: {stats['processed']}")
    print(f"✅ Prefix Matches (Currently Supported): {stats['prefix_match']} ({stats['prefix_match']/stats['processed']*100:.1f}%)")
    print(f"⚠️ Suffix Matches (Currently Missed):    {stats['suffix_match']} ({stats['suffix_match']/stats['processed']*100:.1f}%)")
    print(f"❌ No Infobox Found:                    {stats['no_infobox']} ({stats['no_infobox']/stats['processed']*100:.1f}%)")
    
    total_infoboxes = stats['prefix_match'] + stats['suffix_match']
    print(f"\nPotential Total Coverage: {total_infoboxes} ({total_infoboxes/stats['processed']*100:.1f}%)")
    
    print("\n🔝 Top 10 Suffix Patterns (Missed):")
    for name, count in stats['suffix_examples'].most_common(10):
        print(f"  - {name}: {count}")

    print("\n🔝 Top 5 Prefix Patterns (Caught):")
    for name, count in stats['prefix_examples'].most_common(5):
        print(f"  - {name}: {count}")

if __name__ == "__main__":
    analyze_patterns()
