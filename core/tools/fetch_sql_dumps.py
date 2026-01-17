#!/usr/bin/env python3
"""
WikiGraph Dump Fetcher
Robustly downloads specific SQL dump files from Wikimedia.
"""

import os
import sys
import argparse
import urllib.request
from pathlib import Path
from tqdm import tqdm

# Files required for the "Slim Architecture" metadata tier
REQUIRED_DUMPS = [
    "page",           # ID, Title, Namespace, Is_Redirect
    "categorylinks",  # Article -> Category edges
    "pagelinks",      # Article -> Article edges (Graph Topology)
    "redirect",       # Redirect Source -> Target
    "langlinks",      # Interlingual mapping (to QID)
    "page_props",     # Wikidata QID mapping (pp_propname='wikibase_item')
    "linktarget"      # Target titles for normalized links (replacing cl_to, pl_title)
]

BASE_URL = "https://dumps.wikimedia.org"

def download_file(url, dest_path):
    if dest_path.exists():
        print(f"  ⚠️  Skipping {dest_path.name} (already exists)")
        return

    print(f"  ⬇️  Downloading {dest_path.name}...")
    try:
        with tqdm(unit='B', unit_scale=True, unit_divisor=1024, miniters=1, desc=dest_path.name) as t:
            def update_to(b=1, bsize=1, tsize=None):
                if tsize is not None:
                    t.total = tsize
                t.update(b * bsize - t.n)

            urllib.request.urlretrieve(url, filename=dest_path, reporthook=update_to)
    except Exception as e:
        print(f"  ❌ Error downloading {url}: {e}")
        if dest_path.exists():
            dest_path.unlink()
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Fetch Wikipedia SQL dumps.")
    parser.add_argument("langs", nargs="+", help="Language codes (e.g. en pl)")
    parser.add_argument("--date", default="latest", help="Dump date (default: latest)")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent.parent
    raw_data_dir = project_root / "data" / "raw"
    raw_data_dir.mkdir(parents=True, exist_ok=True)

    print(f"📂 Download Target: {raw_data_dir}")

    for lang in args.langs:
        print(f"\n🌍 Processing language: [{lang.upper()}]")
        
        # 1. Check for the 'latest' redirect if date is 'latest' to get the real date folder (optional, but good for versioning)
        # For simplicity in this robust script, we stick to the provided date tag which works for 'latest' in URL construction.
        
        for dump_type in REQUIRED_DUMPS:
            filename = f"{lang}wiki-{args.date}-{dump_type}.sql.gz"
            url = f"{BASE_URL}/{lang}wiki/{args.date}/{filename}"
            dest_path = raw_data_dir / filename
            
            download_file(url, dest_path)

    print("\n✅ All downloads complete.")

if __name__ == "__main__":
    main()
