import mwxml
import mwparserfromhell
import bz2
from pathlib import Path

def debug_pl():
    path = "data/raw/plwiki-20251201-pages-articles-multistream.xml.bz2"
    if not Path(path).exists():
        path = str(next(Path("data/raw").glob("plwiki-*-pages-articles-multistream.xml.bz2")))
    
    print(f"Debugging templates in: {path}")
    
    with bz2.open(path, 'rt', encoding='utf-8', errors='replace') as f:
        dump = mwxml.Dump.from_file(f)
        count = 0
        for page in dump:
            if page.namespace != 0 or page.redirect: continue
            
            count += 1
            if count > 10: break
            
            try:
                rev = next(page)
                if not rev.text: continue
                wikicode = mwparserfromhell.parse(rev.text)
                templates = wikicode.filter_templates()
                print(f"\nID: {page.id}, Title: {page.title}")
                found_any = False
                for t in templates:
                    name = str(t.name).strip()
                    if "infobox" in name.lower() or "infokarta" in name.lower():
                        print(f"  - [MATCH?] Template: '{name}'")
                        found_any = True
                    else:
                        # Print first 3 non-matching just to see
                        pass
                if not found_any:
                    print("  (No templates containing 'infobox' or 'infokarta' found)")
                    # Print ALL templates to see what they use
                    for t in templates[:5]:
                        print(f"  - Template: '{str(t.name).strip()}'")

            except Exception as e: 
                print(e)

if __name__ == "__main__":
    debug_pl()
