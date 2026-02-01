import mwxml
import mwparserfromhell
import json
import argparse
import sys
import bz2
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.language_manager import LanguageManager

def slow_check(wikitext, prefixes):
    if not wikitext: return False
    parsed = mwparserfromhell.parse(wikitext)
    for template in parsed.filter_templates():
        name = str(template.name).strip()
        if any(name.startswith(p) for p in prefixes):
            return True
    return False

def quick_has_infobox(wikitext, prefixes):
    if not wikitext:
        return False
    # MIRRORING THE IMPLEMENTATION IN extract_infoboxes.py
    for prefix in prefixes:
        if f"{{{{{prefix}" in wikitext:
            return True
    return False

def main():
    lang = 'de'
    limit = 1000
    
    config = LanguageManager.get_config(lang)
    prefixes = config['infobox'].get('template_prefixes', [])
    
    xml_path = Path(f"data/raw/{lang}wiki-latest-pages-articles-multistream.xml.bz2")
    
    print(f"Verifying optimization accuracy for {lang}...")
    print(f"Prefixes: {prefixes}")
    
    missed = 0
    false_positives = 0
    total_infoboxes = 0
    checked = 0
    
    with bz2.open(xml_path, 'rt', encoding='utf-8', errors='replace') as f:
        dump = mwxml.Dump.from_file(f)
        for page in dump:
            if page.namespace != 0 or page.redirect:
                continue
            
            try:
                revision = next(page)
                wikitext = revision.text or ''
                
                has_slow = slow_check(wikitext, prefixes)
                has_fast = quick_has_infobox(wikitext, prefixes)
                
                if has_slow:
                    total_infoboxes += 1
                
                if has_slow and not has_fast:
                    missed += 1
                    print(f"❌ Missed: {page.title}")
                    # Print snippet
                    # print(wikitext[:200])
                
                if not has_slow and has_fast:
                    false_positives += 1
                
                checked += 1
                if checked >= limit:
                    break
            except StopIteration:
                continue

    print(f"\nResults on {checked} articles:")
    print(f"Total Infoboxes (Slow/Correct): {total_infoboxes}")
    print(f"Missed by Fast Check: {missed}")
    print(f"False Positives: {false_positives}")
    
    if missed > 0:
        print(f"Accuracy Fail: Missed {missed} valid infoboxes!")
        sys.exit(1)
    else:
        print("✅ Accuracy Pass: 100% Recall")

if __name__ == "__main__":
    main()
