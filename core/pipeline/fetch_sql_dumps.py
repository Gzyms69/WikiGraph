#!/usr/bin/env python3
"""
WikiGraph Dump Fetcher (Turbo Edition)
Robustly downloads specific SQL and XML dump files from Wikimedia using aria2c for maximum speed.
"""

import os
import sys
import argparse
import subprocess
import shutil
from pathlib import Path

# Files required for the "Slim Architecture" metadata tier
REQUIRED_DUMPS = [
    "page",           # ID, Title, Namespace, Is_Redirect
    "categorylinks",  # Article -> Category edges
    "pagelinks",      # Article -> Article edges (Graph Topology)
    "redirect",       # Redirect Source -> Target
    "langlinks",      # Interlingual mapping (to QID)
    "page_props",     # Wikidata QID mapping (pp_propname='wikibase_item')
    "linktarget",     # Target titles for normalized links (replacing cl_to, pl_title)
    "pages-articles-multistream" # XML content for infobox extraction
]

BASE_URL = "https://dumps.wikimedia.org"

def check_aria2():
    return shutil.which("aria2c") is not None

def download_with_aria2(url_pairs, dest_dir):
    """
    Downloads multiple files using aria2c.
    url_pairs: List of (url, filename)
    """
    input_file = dest_dir / "aria2_input.txt"
    
    print(f"🚀 Turbo Download starting via aria2c...")
    with open(input_file, "w") as f:
        for url, filename in url_pairs:
            f.write(f"{url}\n")
            f.write(f"  out={filename}\n")
    
    # aria2c optimized flags (Polite Mode)
    cmd = [
        "aria2c",
        "--input-file", str(input_file),
        "--dir", str(dest_dir),
        "--continue=true",
        "--max-connection-per-server=4",
        "--split=4",
        "--min-split-size=1M",
        "--max-concurrent-downloads=2",
        "--summary-interval=10",
        "--console-log-level=warn",
        "--user-agent=WikiGraph-ConfigFetcher/1.0 (local development; contact@example.com)"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("\n✅ Turbo Download complete.")
    except subprocess.CalledProcessError as e:
        print(f"❌ aria2c failed with exit code {e.returncode}")
        sys.exit(1)
    finally:
        if input_file.exists():
            input_file.unlink()

def download_fallback(url_pairs, dest_dir):
    """
    Sequential fallback using urllib.
    """
    import urllib.request
    from tqdm import tqdm
    
    print("⚠️  aria2c not found. Falling back to slow sequential download...")
    
    for url, filename in url_pairs:
        dest_path = dest_dir / filename
        if dest_path.exists():
            print(f"  ⚠️  Skipping {filename} (exists)")
            continue
            
        print(f"  ⬇️  Downloading {filename}...")
        try:
            with tqdm(unit='B', unit_scale=True, unit_divisor=1024, miniters=1, desc=filename) as t:
                def update_to(b=1, bsize=1, tsize=None):
                    if tsize is not None:
                        t.total = tsize
                    t.update(b * bsize - t.n)
                urllib.request.urlretrieve(url, filename=dest_path, reporthook=update_to)
        except Exception as e:
            print(f"  ❌ Error: {e}")
            if dest_path.exists(): dest_path.unlink()
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Fetch Wikipedia SQL/XML dumps.")
    parser.add_argument("langs", nargs="+", help="Language codes (e.g. en pl)")
    parser.add_argument("--date", default="latest", help="Dump date (default: latest)")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent.parent
    raw_data_dir = project_root / "data" / "raw"
    raw_data_dir.mkdir(parents=True, exist_ok=True)

    download_queue = []

    for lang in args.langs:
        for dump_type in REQUIRED_DUMPS:
            if "pages-articles" in dump_type:
                ext = ".xml.bz2"
            else:
                ext = ".sql.gz"

            filename = f"{lang}wiki-{args.date}-{dump_type}{ext}"
            url = f"{BASE_URL}/{lang}wiki/{args.date}/{filename}"
            
            # Add to queue
            download_queue.append((url, filename))

    if not download_queue:
        print("Nothing to download.")
        return

    force_seq = os.environ.get("FORCE_SEQUENTIAL", "0") == "1"
    
    if not force_seq and check_aria2():
        download_with_aria2(download_queue, raw_data_dir)
    else:
        download_fallback(download_queue, raw_data_dir)

if __name__ == "__main__":
    main()
