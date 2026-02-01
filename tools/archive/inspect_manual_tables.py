import bz2
import mwxml
import re
from pathlib import Path

def inspect_manual_tables():
    xml_path = Path("data/raw/dewiki-latest-pages-articles-multistream.xml.bz2")
    if not xml_path.exists():
        xml_path = next(Path("data/raw").glob("dewiki-*-pages-articles-multistream.xml.bz2"), None)
    
    if not xml_path:
        print("XML file not found!")
        return

    print(f"Scanning {xml_path} for manual infobox tables...")
    
    # Pattern to detect manual infobox tables
    # Looking for table start with 'infobox' in class
    TABLE_START = re.compile(r'{{|\s*class="[^"]*infobox', re.IGNORECASE)
    
    count = 0
    MAX_EXAMPLES = 10
    
    with bz2.open(xml_path, 'rt', encoding='utf-8', errors='replace') as f:
        dump = mwxml.Dump.from_file(f)
        for page in dump:
            if page.namespace != 0:
                continue
                
            try:
                revision = next(page)
                text = revision.text or ""
                
                if TABLE_START.search(text):
                    print(f"\n[{count+1}] Found Manual Table: '{page.title}' (ID: {page.id})")
                    print("-" * 60)
                    
                    # Extract the table snippet (naive extraction for inspection)
                    match = TABLE_START.search(text)
                    start_idx = match.start()
                    # Find end of table loosely
                    end_idx = text.find("|}}", start_idx)
                    
                    if end_idx != -1:
                        # Print the table content (truncate if huge)
                        snippet = text[start_idx:end_idx+4]
                        if len(snippet) > 2000:
                            print(snippet[:2000] + "\n... [Truncated]")
                        else:
                            print(snippet)
                    else:
                        print(text[start_idx:start_idx+500] + "\n... [End tag missing in snippet]")
                        
                    count += 1
                    if count >= MAX_EXAMPLES:
                        break
            except StopIteration:
                continue
            except Exception as e:
                print(f"Error processing {page.title}: {e}")

if __name__ == "__main__":
    inspect_manual_tables()
