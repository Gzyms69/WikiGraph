#!/usr/bin/env python3
"""
PHASE 1: ULTRA-SAFE MINIMAL STREAMING PARSER
Processes 500 articles per batch with strict memory limits.
Extracts only: IDs, titles, basic links.
Memory-safe: never holds more than 50 articles in RAM.
"""

import bz2
import json
import gzip
import csv
import logging
import re
from pathlib import Path
from datetime import datetime
import psutil
import mwxml
import mwparserfromhell

# ANSI color codes for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

class MinimalParser:
    """Ultra-safe streaming parser with 500-article batches and redirect resolution."""

    def __init__(self):
        self.batch_size = 500  # ULTRA-SAFE: never more than 500 in memory
        self.articles_processed = 0
        self.redirects_found = 0
        self.checkpoint_file = Path('/mnt/c/Users/PC/WikiGraph') / 'processed_batches' / 'checkpoint.json'
        self.redirects_file = Path('/mnt/c/Users/PC/WikiGraph') / 'processed_batches' / 'redirects.json'
        self.redirects = {}  # Cache for redirects
        self.max_redirects = 50000  # Limit cache size
        self.setup_logging()

    def setup_logging(self):
        """Add logging to track progress."""
        log_file = Path('/mnt/c/Users/PC/WikiGraph') / 'logs' / 'parser.log'
        log_file.parent.mkdir(exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.log = logging.getLogger()

    def check_memory(self):
        """Check current memory usage."""
        process = psutil.Process()
        mem_mb = process.memory_info().rss / 1024 / 1024
        return mem_mb

    def load_checkpoint(self):
        """Load last processed article ID."""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('last_article_id', 0)
            except Exception as e:
                self.log.error(f"Failed to load checkpoint: {e}")
        return 0

    def save_checkpoint(self, last_id, batch_num):
        """Save progress checkpoint."""
        checkpoint = {
            'last_article_id': last_id,
            'batch_number': batch_num,
            'articles_processed': self.articles_processed,
            'redirects_found': self.redirects_found,
            'timestamp': datetime.now().isoformat()
        }
        try:
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint, f, indent=2)
        except Exception as e:
            self.log.error(f"Failed to save checkpoint: {e}")

    def save_redirects(self):
        """Save redirects mapping."""
        try:
            with open(self.redirects_file, 'w', encoding='utf-8') as f:
                json.dump(self.redirects, f, ensure_ascii=False, indent=2)
            self.log.info(f"Saved {len(self.redirects)} redirects to file")
        except Exception as e:
            self.log.error(f"Failed to save redirects: {e}")

    def clean_link(self, link_text):
        """Basic link cleaning - remove pipes and anchors."""
        if '|' in link_text:
            link_text = link_text.split('|')[0]
        if '#' in link_text:
            link_text = link_text.split('#')[0]
        return link_text.strip()

    def is_redirect(self, wikitext):
        """Check if article is a redirect and extract target."""
        text = wikitext[:200].lower()  # Check only first 200 chars
        redirect_patterns = [
            r'#(?:redirect|przekieruj)\s*\[\[([^\]]+)\]\]',
            r'#(?:redirect|przekieruj)\s*\[\[([^\|\]]+)',
        ]

        for pattern in redirect_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                target = self.clean_link(match.group(1))
                return target

        return None

    def resolve_redirect(self, link):
        """Resolve link through redirect chain (max 5 hops)."""
        original = link
        visited = set()
        hops = 0
        max_hops = 5

        while link in self.redirects and link not in visited:
            visited.add(link)
            link = self.redirects[link]
            hops += 1

            # Prevent infinite loops
            if hops >= max_hops:
                self.log.warning(f"Redirect chain too long for: {original}")
                return original

        return link

    def process_dump(self, dump_path, output_dir, max_articles=None):
        """Process dump with strict 500-article batches and checkpointing."""

        # Load checkpoint
        last_id = self.load_checkpoint()
        batch_num = 1
        skip_mode = (last_id > 0)

        if skip_mode:
            print(f"{YELLOW}[CHECKPOINT] Resuming from article ID: {last_id}{RESET}")

        articles_buffer = []
        links_buffer = []

        print(f"{YELLOW}[PROCESSING] Opening dump file: {dump_path}{RESET}")
        with bz2.open(dump_path, 'rt', encoding='utf-8') as f:
            dump = mwxml.Dump.from_file(f)

            for page in dump:
                # Skip until we reach checkpoint
                if skip_mode and page.id <= last_id:
                    continue
                skip_mode = False  # Found checkpoint
                # Check memory every 100 articles
                if self.articles_processed % 100 == 0:
                    mem_mb = self.check_memory()
                    if mem_mb > 2000:  # 2GB warning
                        self.log.warning(f"High memory: {mem_mb:.1f}MB")
                    elif self.articles_processed % 500 == 0:
                        self.log.info(f"Processed {self.articles_processed} articles, Memory: {mem_mb:.1f}MB")

                # ONLY process main articles (namespace 0)
                if page.namespace != 0:
                    continue

                for revision in page:
                    # Skip if not enough text
                    if not revision.text:
                        continue

                    # Check for redirect FIRST
                    redirect_target = self.is_redirect(revision.text)
                    if redirect_target:
                        # This is a redirect page - cache it and skip
                        self.redirects[page.title] = redirect_target
                        self.redirects_found += 1

                        # Prune cache if too large
                        if len(self.redirects) > self.max_redirects:
                            keys = list(self.redirects.keys())
                            for key in keys[:self.max_redirects // 10]:
                                del self.redirects[key]

                        # Skip redirect articles from processing
                        continue

                    # EXTRACT BASIC ARTICLE DATA (only for regular articles)
                    article = {
                        'id': page.id,
                        'title': page.title,
                        'revision_id': revision.id
                    }
                    articles_buffer.append(article)

                    # EXTRACT BASIC LINKS with redirect resolution
                    try:
                        wikicode = mwparserfromhell.parse(revision.text)
                        for link in wikicode.filter_wikilinks():
                            link_text = str(link.title).strip()
                            cleaned = self.clean_link(link_text)
                            if cleaned and not cleaned.startswith(('File:', 'Category:')):
                                # RESOLVE REDIRECT immediately
                                resolved = self.resolve_redirect(cleaned)
                                # Skip self-links
                                if resolved != page.title:
                                    links_buffer.append((page.title, resolved))
                    except Exception as e:
                        print(f"{RED}[ERROR] Link extraction failed for {page.title}: {e}{RESET}")
                        pass  # Skip if parsing fails

                    self.articles_processed += 1

                    # WRITE BATCH EVERY 500 ARTICLES
                    if len(articles_buffer) >= self.batch_size:
                        self.write_batch(articles_buffer, links_buffer, batch_num, output_dir)
                        print(f"{GREEN}[SUCCESS] Batch {batch_num}: {len(articles_buffer)} articles, {len(links_buffer)} links{RESET}")

                        # Reset buffers
                        articles_buffer = []
                        links_buffer = []
                        batch_num += 1

                    # STOP if reached max_articles (for testing)
                    if self.articles_processed >= max_articles:
                        print(f"{YELLOW}[INFO] Reached limit of {max_articles} articles{RESET}")
                        break

                if self.articles_processed >= max_articles:
                    break

        # Write final batch
        if articles_buffer:
            self.write_batch(articles_buffer, links_buffer, batch_num, output_dir)
            print(f"{GREEN}[SUCCESS] Final batch {batch_num}: {len(articles_buffer)} articles, {len(links_buffer)} links{RESET}")

    def write_batch(self, articles, links, batch_num, output_dir):
        """Write batch to compressed files."""
        # Write articles to JSONL.gz
        articles_file = output_dir / f"articles_batch_{batch_num:04d}.jsonl.gz"
        with gzip.open(articles_file, 'wt', encoding='utf-8') as f:
            for article in articles:
                f.write(json.dumps(article, ensure_ascii=False) + '\n')

        # Write links to CSV.gz
        links_file = output_dir / f"links_batch_{batch_num:04d}.csv.gz"
        with gzip.open(links_file, 'wt', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(links)

        # Save checkpoint after each batch
        if articles:
            last_article_id = articles[-1]['id']
            self.save_checkpoint(last_article_id, batch_num)

def main():
    """Main execution with configurable article limit."""
    import argparse

    parser = argparse.ArgumentParser(description='Polish Wikipedia Parser')
    parser.add_argument('--max-articles', type=int, default=1000,
                       help='Maximum articles to process (default: 1000)')
    parser.add_argument('--test-name', type=str, default='Ultra-Safe 500 Batch Test',
                       help='Test name for logging')

    args = parser.parse_args()

    base_dir = Path('/mnt/c/Users/PC/WikiGraph')
    dump_path = base_dir / 'raw_data_wiki' / 'plwiki-20251201-pages-articles-multistream.xml.bz2'
    output_dir = base_dir / 'processed_batches'

    # Validate inputs
    if not dump_path.exists():
        print(f"{RED}[ERROR] Dump file not found: {dump_path}{RESET}")
        return

    print(f"{GREEN}==> PHASE 1 MINIMAL PARSER - {args.test_name}{RESET}")
    print("=" * 60)
    print(f"{BLUE}[FILE] Data source: {dump_path}{RESET}")
    print(f"{BLUE}[FILE] Output directory: {output_dir}{RESET}")
    print(f"{YELLOW}[CONFIG] Batch size: 500 articles{RESET}")
    print(f"{YELLOW}[CONFIG] Test limit: {args.max_articles:,} articles{RESET}")
    print("=" * 60)

    wiki_parser = MinimalParser()

    # Check initial memory
    initial_mem = wiki_parser.check_memory()
    print(f"{BLUE}[MEMORY] Initial memory usage: {initial_mem:.1f}MB{RESET}")

    wiki_parser.process_dump(dump_path, output_dir, max_articles=args.max_articles)

    # Check final memory
    final_mem = wiki_parser.check_memory()
    print(f"{BLUE}[MEMORY] Final memory usage: {final_mem:.1f}MB{RESET}")
    print(f"{BLUE}[MEMORY] Memory delta: {final_mem - initial_mem:.1f}MB{RESET}")

    # Save final checkpoint
    print(f"{BLUE}[CHECKPOINT] Saving final checkpoint...{RESET}")
    wiki_parser.save_checkpoint(0, 0)  # Final checkpoint

    print(f"{BLUE}[REDIRECTS] Saving redirects mapping...{RESET}")
    wiki_parser.save_redirects()

    print(f"\n{GREEN}[SUCCESS] Processing Complete{RESET}")
    print(f"{BLUE}[STATS] Total articles processed: {wiki_parser.articles_processed:,}{RESET}")
    print(f"{BLUE}[STATS] Total redirects found: {wiki_parser.redirects_found:,}{RESET}")
    print(f"{BLUE}[STATS] Redirects in cache: {len(wiki_parser.redirects):,}{RESET}")
    print(f"{BLUE}[CHECKPOINT] Progress saved to: {wiki_parser.checkpoint_file}{RESET}")
    print(f"{BLUE}[REDIRECTS] Redirects saved to: {wiki_parser.redirects_file}{RESET}")

if __name__ == "__main__":
    main()
