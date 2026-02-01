import bz2
import mwxml
from pathlib import Path

def inspect_page():
    xml_path = Path("data/raw/dewiki-latest-pages-articles-multistream.xml.bz2")
    if not xml_path.exists():
        xml_path = next(Path("data/raw").glob("dewiki-*-pages-articles-multistream.xml.bz2"), None)
    
    if not xml_path:
        print("XML file not found!")
        return

    TARGET = "Donald Tusk"
    print(f"Scanning {xml_path} for '{TARGET}'...")
    
    with bz2.open(xml_path, 'rt', encoding='utf-8', errors='replace') as f:
        dump = mwxml.Dump.from_file(f)
        for page in dump:
            if page.title == TARGET and page.namespace == 0:
                print(f"✅ Found '{TARGET}' (ID: {page.id})")
                revision = next(page)
                text = revision.text
                print("\n--- Wikitext Start ---")
                print(text[:1000])
                print("\n--- Wikitext End ---")
                return

if __name__ == "__main__":
    inspect_page()

