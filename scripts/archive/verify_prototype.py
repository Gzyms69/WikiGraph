#!/usr/bin/env python3
"""
Verify the prototype output.
"""

import json
from pathlib import Path

# ANSI color codes for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

def verify_output():
    """Verify the prototype output file."""
    output_path = Path('/mnt/c/Users/PC/WikiGraph') / 'test_output_100.jsonl'

    if not output_path.exists():
        print(f"{RED}[ERROR] Output file not found at {output_path}!{RESET}")
        return

    articles = []
    with open(output_path, 'r', encoding='utf-8') as f:
        for line in f:
            articles.append(json.loads(line.strip()))

    print(f"{GREEN}[SUCCESS] Total articles processed: {len(articles)}{RESET}")
    print(f"\n{YELLOW}[VALIDATION] Sample articles:{RESET}")
    print("-" * 60)

    for i, article in enumerate(articles[:5]):
        print(f"{i+1}. {article['title']} (ID: {article['id']})")
        print(f"   Links: {len(article['links'])} links")
        print(f"   Infobox: {article['infobox'] or 'None'}")
        print(f"   Text length: {article['text_length']} chars")
        if article['links']:
            print(f"   First link: {article['links'][0]}")
        print()

    print("-" * 60)
    print(f"{BLUE}[STATS] Unique infobox types found:{RESET}")
    infoboxes = set(a['infobox'] for a in articles if a['infobox'])
    for ib in infoboxes:
        print(f"  - {ib}")

    total_links = sum(len(a['links']) for a in articles)
    print(f"\n{BLUE}[STATS] Total links extracted: {total_links}{RESET}")

    # Validation checks
    print(f"\n{YELLOW}[VALIDATION] CHECKLIST:{RESET}")
    checks = [
        (len(articles) == 100, "Exactly 100 articles processed"),
        (all(isinstance(a.get('id'), int) for a in articles), "All articles have integer IDs"),
        (all(a.get('title') for a in articles), "All articles have titles"),
        (all(isinstance(a.get('links', []), list) for a in articles), "All articles have links array"),
        (total_links > 0, "Links were extracted"),
    ]

    for check, description in checks:
        status = f"{GREEN}[PASS]{RESET}" if check else f"{RED}[FAIL]{RESET}"
        print(f"  {status} {description}")

if __name__ == "__main__":
    verify_output()
