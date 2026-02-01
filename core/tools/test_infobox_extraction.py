import mwxml
import mwparserfromhell
import sys
import os
import time
import bz2
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())
from config.language_manager import LanguageManager

def process_dump(lang_code, limit=25):
    print(f"\n=== Processing {lang_code.upper()} XML (First {limit} valid articles) ===")
    
    # 1. Load Config
    try:
        config = LanguageManager.get_config(lang_code)
        prefixes = config['infobox']['template_prefixes']
        param_map = config['infobox'].get('parameter_map', {})
        print(f"Loaded config. Prefixes: {prefixes}")
        if param_map:
            print(f"Parameter map loaded ({len(param_map)} entries)")
    except Exception as e:
        print(f"❌ Config Error: {e}")
        return

    # 2. Locate Dump
    dump_path = Path(f"data/raw/{lang_code}wiki-latest-pages-articles-multistream.xml.bz2")
    if not dump_path.exists():
        # Try fallback name (timestamped)
        dump_path = next(Path("data/raw").glob(f"{lang_code}wiki-*-pages-articles-multistream.xml.bz2"), None)
        
    if not dump_path or not dump_path.exists():
        print(f"❌ Dump file not found for {lang_code}")
        return
        
    print(f"Reading: {dump_path}")

    # 3. Stream & Parse
    valid_count = 0
    skipped_ns = 0
    skipped_redirect = 0
    
    start_time = time.time()
    
    try:
        # Use bz2.open to handle compression transparently
        with bz2.open(dump_path, 'rt', encoding='utf-8', errors='replace') as f:
            dump = mwxml.Dump.from_file(f)
            
            for page in dump:
                # STOP Condition
                if valid_count >= limit:
                    break
                
                # Filter: Namespace 0 (Articles)
                if page.namespace != 0:
                    skipped_ns += 1
                    continue
                
                # Filter: Redirects
                if page.redirect:
                    skipped_redirect += 1
                    continue
                
                # Process Valid Article
                valid_count += 1
                
                # Parse Revision
                try:
                    # Get the last revision
                    revision = next(page)
                    
                    if not revision.text:
                        continue
                        
                    wikicode = mwparserfromhell.parse(revision.text)
                    templates = wikicode.filter_templates()
                    
                    infoboxes = []
                    for t in templates:
                        name = str(t.name).strip()
                        # Check against prefixes
                        if any(name.startswith(p) for p in prefixes):
                            params = {}
                            for param in t.params:
                                p_name = str(param.name).strip()
                                p_val = str(param.value).strip()
                                
                                # Apply mapping
                                if p_name in param_map:
                                    p_name = param_map[p_name]
                                    
                                # Truncate long values for display
                                params[p_name] = p_val[:50] + "..." if len(p_val) > 50 else p_val
                                
                            infoboxes.append({'name': name, 'params': params})
                    
                    # Output
                    print(f"[{valid_count}/{limit}] ID: {page.id}, Title: '{page.title}'")
                    if infoboxes:
                        print(f"  Found {len(infoboxes)} infobox templates:")
                        for box in infoboxes:
                            print(f"  - {box['name']}: {box['params']}")
                    else:
                        print("  No infoboxes found.")
                        
                except StopIteration:
                    print(f"  ⚠️ No revision found for {page.title}")
                except Exception as e:
                    print(f"  ❌ Parse Error for {page.title}: {e}")
                
    except Exception as e:
        print(f"❌ Stream Error: {e}")

    duration = time.time() - start_time
    print(f"\n--- Stats for {lang_code.upper()} ---")
    print(f"Processed: {valid_count}")
    print(f"Skipped (Namespace): {skipped_ns}")
    print(f"Skipped (Redirect): {skipped_redirect}")
    print(f"Time: {duration:.2f}s")

if __name__ == "__main__":
    process_dump('pl', 25)
    process_dump('de', 25)
