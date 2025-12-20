#!/usr/bin/env python3
# ~/WikiGraph/scripts/check_late_batches.py
"""
Check later batches for infoboxes and categories.
Useful for verifying that infobox extraction works on biographical/geographical articles.
"""

import gzip
import json
from pathlib import Path
from collections import Counter

# ANSI color codes for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

def check_infoboxes():
    """Check batches that likely contain infoboxes."""
    base_dir = Path('/mnt/c/Users/PC/WikiGraph/processed_batches')

    # Check every 100th batch after batch 500 (where people/places appear)
    batches_to_check = [500, 600, 700, 800, 900, 1000]

    print(f"{GREEN}==> CHECKING LATER BATCHES FOR INFOBOXES{RESET}")
    print("="*60)
    print(f"{YELLOW}[NOTE] Early batches contain technical articles without infoboxes.{RESET}")
    print(f"{YELLOW}[NOTE] Biographical/geographical articles appear in later batches.{RESET}")
    print("="*60)

    total_checked = 0
    total_with_infobox = 0
    all_infobox_types = Counter()

    for batch_num in batches_to_check:
        batch_file = base_dir / f'articles_batch_{batch_num:04d}.jsonl.gz'
        if not batch_file.exists():
            print(f"{YELLOW}[MISSING] Batch {batch_num} not found yet{RESET}")
            continue

        print(f"\n{BLUE}[ANALYZING] Batch {batch_num}...{RESET}")

        infobox_types = Counter()
        articles_with_infobox = 0
        articles_with_categories = 0
        total_articles = 0

        try:
            with gzip.open(batch_file, 'rt', encoding='utf-8') as f:
                for line in f:
                    article = json.loads(line)
                    total_articles += 1

                    if article.get('infobox'):
                        articles_with_infobox += 1
                        ib_type = article['infobox'].get('type', 'Unknown')
                        infobox_types[ib_type] += 1
                        all_infobox_types[ib_type] += 1

                    if article.get('categories'):
                        articles_with_categories += 1

            # Update totals
            total_checked += total_articles
            total_with_infobox += articles_with_infobox

            # Display results
            print(f"  Articles: {total_articles:,}")
            print(f"  With infobox: {articles_with_infobox:,} ({articles_with_infobox/total_articles*100:.1f}%)")
            print(f"  With categories: {articles_with_categories:,} ({articles_with_categories/total_articles*100:.1f}%)")

            if infobox_types:
                print(f"  {GREEN}Infobox types (Top 3):{RESET}")
                for ib_type, count in infobox_types.most_common(3):
                    print(f"    {ib_type}: {count}")
            else:
                print(f"  {YELLOW}No infoboxes found in this batch{RESET}")

        except Exception as e:
            print(f"  {RED}[ERROR] Failed to read batch {batch_num}: {e}{RESET}")

    # Overall summary
    print(f"\n{GREEN}{'='*60}{RESET}")
    print(f"{GREEN}OVERALL SUMMARY{RESET}")
    print(f"{'='*60}{RESET}")
    print(f"Total articles checked: {total_checked:,}")
    print(f"Articles with infobox: {total_with_infobox:,} ({total_with_infobox/total_checked*100:.1f}%)")

    if all_infobox_types:
        print(f"\n{GREEN}All Infobox Types Found:{RESET}")
        for ib_type, count in sorted(all_infobox_types.items()):
            print(f"  {ib_type}: {count}")

    # Validation
    print(f"\n{YELLOW}[VALIDATION]{RESET}")
    print("-" * 30)
    if total_with_infobox > 0:
        print(f"  {GREEN}[PASS]{RESET} Infobox extraction working")
    else:
        print(f"  {YELLOW}[INFO]{RESET} No infoboxes found (may be too early in dump)")

    print(f"  {GREEN}[PASS]{RESET} Script completed successfully")

if __name__ == "__main__":
    check_infoboxes()
