import mwxml
import mwparserfromhell
import bz2
import json
from collections import Counter

DUMP_PATH = 'data/raw/dewiki-latest-pages-articles-multistream.xml.bz2'
LIMIT = 50000

TARGET_TEMPLATES = {
    'Person', 'Jahresbox', 'Taxobox', 'Chembox', 'Personendaten', 
    'Geobox', 'Filmbox', 'Musikbox'
}

def classify_templates():
    print(f"🔬 Starting Targeted Template Classification on first {LIMIT} articles...")
    print(f"🎯 Targets: {TARGET_TEMPLATES}\n")
    
    samples_found = {t: [] for t in TARGET_TEMPLATES}
    counts = Counter()
    processed = 0

    try:
        with bz2.open(DUMP_PATH, 'rt', encoding='utf-8', errors='ignore') as f:
            dump = mwxml.Dump.from_file(f)
            
            for page in dump:
                if page.namespace != 0: continue
                
                for revision in page:
                    processed += 1
                    text = revision.text or ""
                    
                    # Quick string check optimization
                    if not any(t in text for t in TARGET_TEMPLATES):
                        if processed >= LIMIT: break
                        continue

                    wikicode = mwparserfromhell.parse(text)
                    templates = wikicode.filter_templates()
                    
                    for t in templates:
                        name = str(t.name).strip()
                        # Check exact match or closely related variants
                        # (e.g., 'Taxobox' matches 'Taxobox')
                        clean_name = name.split('\n')[0].strip() # Handle multiline garbage
                        
                        target_hit = None
                        for target in TARGET_TEMPLATES:
                            if clean_name == target:
                                target_hit = target
                                break
                        
                        if target_hit:
                            counts[target_hit] += 1
                            if len(samples_found[target_hit]) < 3:
                                # Extract params for classification
                                params = {}
                                for p in t.params[:5]: # First 5 params
                                    params[str(p.name).strip()] = str(p.value).strip()[:50]
                                samples_found[target_hit].append({
                                    'article': page.title,
                                    'params': params
                                })

                    if processed >= LIMIT:
                        break
                if processed >= LIMIT:
                    break

    except FileNotFoundError:
        print(f"❌ Dump file not found: {DUMP_PATH}")
        return

    print("="*50)
    print("📊 CLASSIFICATION RESULTS")
    print("="*50)
    
    for target in TARGET_TEMPLATES:
        count = counts[target]
        print(f"\n🔹 Template: {{{{{target}}}}}")
        print(f"   Found: {count} times in {LIMIT} articles")
        
        if count == 0:
            print("   (No samples found)")
            continue
            
        print("   🔍 Structure Analysis:")
        for idx, sample in enumerate(samples_found[target]):
            print(f"     Sample {idx+1} ({sample['article']}):")
            if not sample['params']:
                print("       [No parameters / Empty]")
            for k, v in sample['params'].items():
                print(f"       - {k}: {v}...")

if __name__ == "__main__":
    classify_templates()
