import mwxml
import mwparserfromhell
import bz2
from collections import Counter

DUMP_PATH = 'data/raw/dewiki-latest-pages-articles-multistream.xml.bz2'
LIMIT = 50000

# Templates we already know about or want to ignore in the final list
KNOWN_PATTERNS = {'Infobox', 'Taxobox', 'Personendaten'} 
IGNORE_LIST = {
    'Internetquelle', 'Literatur', 'Webarchiv', 'lang', 'Zitat', 'Anker',
    'Hauptartikel', 'Commonscat', 'Normdaten', 'Wiktionary', 'DNB-Portal',
    'B', 'Siehe auch', 'Hinweis Seiten-Koordinaten', 'Google Buch', '0',
    'Mehrere Bilder', 'YouTube', 'IMDb', 'War lückenhaft', 'Überarbeiten'
}

def discover_hidden():
    print(f"🔬 Starting 'Dark Matter' Template Discovery on first {LIMIT} articles...")
    
    hidden_candidates = Counter()
    processed = 0
    missed_articles = 0

    try:
        with bz2.open(DUMP_PATH, 'rt', encoding='utf-8', errors='ignore') as f:
            dump = mwxml.Dump.from_file(f)
            
            for page in dump:
                if page.namespace != 0: continue
                
                for revision in page:
                    processed += 1
                    text = revision.text or ""
                    
                    # Basic Redirect Filter
                    if text.upper().startswith("#REDIRECT") or text.upper().startswith("#WEITERLEITUNG"):
                        continue

                    wikicode = mwparserfromhell.parse(text)
                    templates = wikicode.filter_templates()
                    
                    has_known = False
                    article_templates = []

                    for t in templates:
                        name = str(t.name).strip().split('\n')[0]
                        article_templates.append(name)
                        
                        # Check if this article is already "covered"
                        if name.startswith("Infobox") or name == "Taxobox" or name == "Personendaten":
                            has_known = True
                    
                    if not has_known:
                        missed_articles += 1
                        for t_name in set(article_templates): # set() to count once per article
                            if len(t_name) > 2 and t_name not in IGNORE_LIST and not t_name.startswith("Vor"):
                                hidden_candidates[t_name] += 1

                    if processed >= LIMIT: break
                if processed >= LIMIT: break

    except FileNotFoundError:
        print(f"❌ Dump file not found: {DUMP_PATH}")
        return

    print("="*50)
    print("📊 DISCOVERY RESULTS (German Wikipedia)")
    print("="*50)
    print(f"Processed: {processed}")
    print(f"Articles with NO Known Infobox: {missed_articles} ({missed_articles/processed*100:.1f}%)")
    
    print("\n🔝 Top 50 Potential Hidden Infoboxes (Filtered):")
    for name, count in hidden_candidates.most_common(50):
        print(f"  - {name}: {count}")

if __name__ == "__main__":
    discover_hidden()
