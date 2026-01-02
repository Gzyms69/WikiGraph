#!/usr/bin/env python3
import bz2
import mwxml
import csv
import argparse
from pathlib import Path
from tqdm import tqdm
import rapidgzip

def extract_redirects(lang, base_dir):
    print(f"--- Extracting Redirects for {lang.upper()} ---")
    raw_dir = base_dir / 'data' / 'raw'
    processed_dir = base_dir / 'data' / 'processed' / lang
    
    # Identify dump
    if lang == 'pl': dbname = 'plwiki'
    elif lang == 'de': dbname = 'dewiki'
    elif lang == 'en': dbname = 'enwiki'
    else: dbname = f"{lang}wiki"
    
    dump_path = next(raw_dir.glob(f'{dbname}-*-pages-articles-multistream.xml.bz2'))
    output_path = processed_dir / 'redirects_verified.csv'
    
    count = 0
    with rapidgzip.open(dump_path, parallelization=4) as f:
        dump = mwxml.Dump.from_file(f)
        with open(output_path, 'w', encoding='utf-8') as out_f:
            writer = csv.writer(out_f)
            for page in tqdm(dump):
                if page.namespace == 0 and page.redirect:
                    writer.writerow([page.title, page.redirect])
                    count += 1
    print(f"✓ Found {count:,} redirects. Saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--lang', required=True)
    args = parser.parse_args()
    extract_redirects(args.lang, Path(__file__).parent.parent.parent)
