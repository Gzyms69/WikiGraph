#!/usr/bin/env python3
"""
PHASE 1 PARSER V1 - Improved streaming extraction of 100 articles
Uses mwxml for streaming XML parsing and mwparserfromhell for wikitext parsing
Enhanced version with better error handling, type hints, and comprehensive extraction
"""

import bz2
import json
import mwxml
import mwparserfromhell
from pathlib import Path
import sys
from typing import Dict, List, Optional, Generator

# ANSI color codes for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

def extract_links(wikicode: mwparserfromhell.wikicode.Wikicode) -> List[str]:
    """Extract internal wiki links from wikitext."""
    links = []
    for link in wikicode.filter_wikilinks():
        # Get the link target (remove any pipe, anchors, etc.)
        target = str(link.title).strip()

        # Skip external links, files, categories, etc.
        if target.startswith(('http:', 'https:', 'File:', 'Image:',
                             'Category:', 'Template:', 'Wikipedia:')):
            continue

        # Remove section anchors (everything after #)
        if '#' in target:
            target = target.split('#')[0]

        # Remove any namespace prefixes if present
        # but keep Polish diacritics
        target = target.strip()
        if target:
            links.append(target)

    return links

def extract_infobox_name(wikicode: mwparserfromhell.wikicode.Wikicode) -> Optional[str]:
    """Extract the name of the first infobox template."""
    for template in wikicode.filter_templates():
        template_name = str(template.name).strip()
        if template_name.lower().startswith('infobox'):
            # Return just the infobox type (e.g., 'Infobox settlement')
            return template_name
    return None

def process_dump(dump_path: str, max_articles: int = 100) -> Generator[Dict, None, None]:
    """Stream and process Wikipedia dump articles."""
    articles_processed = 0

    print(f"{YELLOW}[PROCESSING] Opening dump file: {dump_path}{RESET}")
    with bz2.open(dump_path, 'rt', encoding='utf-8') as f:
        dump = mwxml.Dump.from_file(f)

        for page in dump:
            # Only process main namespace articles (namespace 0)
            if page.namespace != 0:
                continue

            for revision in page:
                try:
                    wikicode = mwparserfromhell.parse(revision.text)

                    # Extract data
                    article_data = {
                        'id': page.id,
                        'title': page.title,
                        'links': extract_links(wikicode)[:5],  # First 5 links
                        'infobox': extract_infobox_name(wikicode),
                        'revision_id': revision.id,
                        'text_length': len(revision.text)
                    }

                    yield article_data
                    articles_processed += 1

                    if articles_processed >= max_articles:
                        print(f"\n{YELLOW}[INFO] Reached limit of {max_articles} articles{RESET}")
                        return

                except Exception as e:
                    print(f"{RED}[ERROR] Error processing article {page.title}: {e}{RESET}")
                    continue

def main():
    """Main execution function."""
    print(f"{GREEN}==> PHASE 1 PARSER V1 - Streaming 100 Articles Test{RESET}")
    print("=" * 60)

    # Set up paths
    base_dir = Path('/mnt/c/Users/PC/WikiGraph')
    dump_path = base_dir / 'raw_data_wiki' / 'plwiki-20251201-pages-articles-multistream.xml.bz2'
    output_path = base_dir / 'test_output_100.jsonl'

    # Validate paths
    if not dump_path.exists():
        print(f"{RED}[ERROR] Dump file not found at {dump_path}{RESET}")
        print(f"{BLUE}[INFO] Please ensure the raw data file exists in ~/WikiGraph/raw_data_wiki/{RESET}")
        sys.exit(1)

    print(f"{BLUE}[FILE] Data source: {dump_path}{RESET}")
    print(f"{BLUE}[FILE] Output will be saved to: {output_path}{RESET}")

    # Process articles
    articles_processed = 0
    with open(output_path, 'w', encoding='utf-8') as outfile:
        for article in process_dump(str(dump_path)):
            # Print to console
            print(f"\n{BLUE}[ARTICLE] [{article['id']}] {article['title']}{RESET}")
            print(f"  Links: {', '.join(article['links'][:3])}" +
                  ("..." if len(article['links']) > 3 else ""))
            print(f"  Infobox: {article['infobox'] or 'None'}")
            print(f"  Text length: {article['text_length']} chars")

            # Save to JSONL file
            json_line = json.dumps(article, ensure_ascii=False)
            outfile.write(json_line + '\n')

            articles_processed += 1

    print(f"\n{GREEN}[SUCCESS] Processed {articles_processed} articles{RESET}")
    print(f"{BLUE}[FILE] Output saved to: {output_path}{RESET}")
    print("="*60)

if __name__ == "__main__":
    main()
