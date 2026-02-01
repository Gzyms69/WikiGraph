import mwxml
import mwparserfromhell
import bz2
from collections import Counter
from pathlib import Path

DUMP_PATH = 'data/raw/dewiki-latest-pages-articles-multistream.xml.bz2'
LIMIT = 20000

def audit_patterns():
    print(f"🔬 Starting German Pattern Audit on first {LIMIT} articles...")
    
    stats = {
        'processed': 0,
        'current_match': 0,
        'vorlage_match': 0,
        'suffix_match': 0,
        'no_match': 0
    }
    
    # Track templates in articles that seemingly have NO infobox
    missed_opportunity_templates = Counter()

    try:
        with bz2.open(DUMP_PATH, 'rt', encoding='utf-8', errors='ignore') as f:
            dump = mwxml.Dump.from_file(f)
            
            for page in dump:
                if page.namespace != 0: continue
                
                for revision in page:
                    text = revision.text or ""
                    if text.upper().startswith("#REDIRECT") or text.upper().startswith("#WEITERLEITUNG"):
                        continue

                    stats['processed'] += 1
                    
                    wikicode = mwparserfromhell.parse(text)
                    templates = wikicode.filter_templates()
                    
                    has_match = False
                    has_vorlage = False
                    has_suffix = False
                    
                    page_templates = []

                    for t in templates:
                        name = str(t.name).strip()
                        page_templates.append(name)
                        
                        # 1. Current Logic (Infobox ...)
                        if name.startswith("Infobox"):
                            has_match = True
                        
                        # 2. Hypothesis A (Vorlage:Infobox ...)
                        if name.startswith("Vorlage:Infobox"):
                            has_vorlage = True
                            
                        # 3. Hypothesis B (... infobox)
                        if name.lower().endswith("infobox") and not name.startswith("Infobox"):
                            has_suffix = True

                    if has_match:
                        stats['current_match'] += 1
                    elif has_vorlage:
                        stats['vorlage_match'] += 1
                    elif has_suffix:
                        stats['suffix_match'] += 1
                    else:
                        stats['no_match'] += 1
                        # Log top templates for this "missed" article
                        for t_name in page_templates:
                            missed_opportunity_templates[t_name] += 1

                    if stats['processed'] % 2000 == 0:
                        print(f"   ... {stats['processed']} processed. Match: {stats['current_match']} | No Match: {stats['no_match']}")

                    if stats['processed'] >= LIMIT:
                        break
                
                if stats['processed'] >= LIMIT:
                    break

    except FileNotFoundError:
        print(f"❌ Dump file not found: {DUMP_PATH}")
        return

    print("\n" + "="*50)
    print("📊 GERMAN AUDIT RESULTS")
    print("="*50)
    print(f"Total Canonical Articles: {stats['processed']}")
    print(f"✅ Current 'Infobox' Match: {stats['current_match']} ({stats['current_match']/stats['processed']*100:.1f}%)")
    print(f"🔍 'Vorlage:Infobox' Match: {stats['vorlage_match']} ({stats['vorlage_match']/stats['processed']*100:.1f}%)")
    print(f"🔍 Suffix '...infobox' Match: {stats['suffix_match']} ({stats['suffix_match']/stats['processed']*100:.1f}%)")
    print(f"❌ No Match Found:          {stats['no_match']} ({stats['no_match']/stats['processed']*100:.1f}%)")
    
    print("\n🔝 Top 20 Templates in 'No Match' Articles (Potential Misses):")
    for name, count in missed_opportunity_templates.most_common(20):
        print(f"  - {name}: {count}")

if __name__ == "__main__":
    audit_patterns()
