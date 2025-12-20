#!/usr/bin/env python3
"""
PHASE 1: ENHANCED PARSER WITH INFOBOX & CATEGORIES
Inherits from MinimalParser and adds:
- Infobox extraction (structured JSON)
- Categories extraction
- Plain text extraction with word count
- Enhanced article metadata
"""

import bz2
import json
import gzip
import csv
import logging
import re
import sys
from pathlib import Path
from datetime import datetime
import psutil
import mwxml
import mwparserfromhell

# Add config directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config.language_manager import LanguageManager

# ANSI color codes for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

class MinimalParser:
    """Base parser class with core functionality."""

    def __init__(self, lang_code='pl'):
        self.lang_code = lang_code
        self.batch_size = 500
        self.articles_processed = 0
        self.redirects_found = 0

        # Language-aware file paths
        base_dir = Path('/mnt/c/Users/PC/WikiGraph')
        self.checkpoint_file = base_dir / f'processed_batches_{lang_code}' / 'checkpoint.json'
        self.redirects_file = base_dir / f'processed_batches_{lang_code}' / 'redirects.json'
        self.redirects = {}
        self.max_redirects = 50000
        self.setup_logging()

    def setup_logging(self):
        log_file = Path('/mnt/c/Users/PC/WikiGraph') / 'logs' / 'parser.log'
        log_file.parent.mkdir(exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            handlers=[logging.FileHandler(log_file), logging.StreamHandler()]
        )
        self.log = logging.getLogger()

    def check_memory(self):
        process = psutil.Process()
        mem_mb = process.memory_info().rss / 1024 / 1024
        return mem_mb

    def save_checkpoint(self, last_id, batch_num):
        checkpoint = {
            'last_article_id': last_id,
            'batch_number': batch_num,
            'articles_processed': self.articles_processed,
            'redirects_found': self.redirects_found,
            'timestamp': datetime.now().isoformat()
        }
        with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, indent=2)

    def save_redirects(self):
        with open(self.redirects_file, 'w', encoding='utf-8') as f:
            json.dump(self.redirects, f, ensure_ascii=False, indent=2)
        self.log.info(f"Saved {len(self.redirects)} redirects to file")

class EnhancedParser(MinimalParser):
    """Enhanced parser with infobox, categories, and plain text extraction."""

    def extract_infobox(self, wikitext):
        """Extract infobox data as structured JSON."""
        try:
            # Find infobox template
            infobox_match = re.search(r'\{\{Infobox\s+([^\n|]+)', wikitext, re.IGNORECASE)
            if not infobox_match:
                return None

            infobox_type = infobox_match.group(1).strip()

            # For now, just return basic type - full parsing would be complex
            # This gives us the infobox type for categorization
            return {'type': infobox_type}

        except Exception as e:
            self.log.debug(f"Infobox extraction error: {e}")
            return None

    def extract_categories(self, wikitext):
        """Extract category links using language-specific prefixes."""
        categories = []
        # Get language-specific category prefixes
        category_prefixes = LanguageManager.get_namespace_prefixes(self.lang_code).get('category', ['Category:'])

        # Create pattern for all category prefixes
        prefix_pattern = '|'.join(re.escape(prefix.rstrip(':')) for prefix in category_prefixes)
        pattern = rf'\[\[\s*(?:{prefix_pattern})\s*:\s*([^\]|]+)'

        category_matches = re.findall(pattern, wikitext, re.IGNORECASE)
        for cat in category_matches:
            categories.append(cat.strip())
        return categories

    def extract_plain_text(self, wikitext):
        """Extract plain text by removing wiki markup."""
        try:
            # Remove templates {{...}}
            text = re.sub(r'\{\{.*?\}\}', '', wikitext, flags=re.DOTALL)

            # Simplify links [[link|text]] -> text
            text = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', text)

            # Remove simple links [[link]] -> link
            text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)

            # Remove bold/italic ''
            text = re.sub(r"''+", '', text)

            # Remove HTML tags
            text = re.sub(r'<.*?>', '', text)

            # Remove file/image links using language-specific patterns
            cleanup_patterns = LanguageManager.get_text_cleanup_patterns(self.lang_code)
            for pattern in cleanup_patterns:
                text = re.sub(rf'\[\[{pattern}:.*?\]\]', '', text, flags=re.IGNORECASE)

            # Clean up whitespace
            text = re.sub(r'\n+', ' ', text)
            text = re.sub(r'\s+', ' ', text)

            return text.strip()

        except Exception as e:
            self.log.debug(f"Plain text extraction error: {e}")
            return ""

    def clean_link(self, link_text):
        """Basic link cleaning - remove pipes and anchors."""
        if '|' in link_text:
            link_text = link_text.split('|')[0]
        if '#' in link_text:
            link_text = link_text.split('#')[0]
        return link_text.strip()

    def is_redirect(self, wikitext):
        """Check if article is a redirect using language-specific keywords."""
        text = wikitext[:200].lower()
        redirect_keywords = LanguageManager.get_redirect_keywords(self.lang_code)

        # Create patterns dynamically from config
        redirect_patterns = []
        for keyword in redirect_keywords:
            redirect_patterns.extend([
                rf'#(?:{keyword})\s*\[\[([^\]]+)\]\]',
                rf'#(?:{keyword})\s*\[\[([^\|\]]+)',
            ])

        for pattern in redirect_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                target = self.clean_link(match.group(1))
                return target
        return None

    def resolve_redirect(self, link):
        """Resolve redirect chains."""
        original = link
        visited = set()
        hops = 0
        max_hops = 5

        while link in self.redirects and link not in visited:
            visited.add(link)
            link = self.redirects[link]
            hops += 1
            if hops >= max_hops:
                self.log.warning(f"Redirect chain too long for: {original}")
                return original
        return link

    def process_article(self, page, revision):
        """Process single article with enhanced extraction."""
        # Check for redirect
        redirect_target = self.is_redirect(revision.text)
        if redirect_target:
            self.redirects[page.title] = redirect_target
            self.redirects_found += 1
            if len(self.redirects) > self.max_redirects:
                keys = list(self.redirects.keys())
                for key in keys[:self.max_redirects // 10]:
                    del self.redirects[key]
            return None

        # Extract enhanced data
        plain_text = self.extract_plain_text(revision.text)
        word_count = len(plain_text.split()) if plain_text else 0

        article_data = {
            'id': page.id,
            'title': page.title,
            'language': self.lang_code,  # Multi-language support
            'revision_id': revision.id,
            'timestamp': str(revision.timestamp) if revision.timestamp else None,
            'infobox': self.extract_infobox(revision.text),
            'categories': self.extract_categories(revision.text),
            'word_count': word_count,
            'text_length': len(revision.text)
        }

        # Extract links with redirect resolution
        links = []
        try:
            wikicode = mwparserfromhell.parse(revision.text)
            # Get language-specific namespace prefixes to skip
            skip_prefixes = LanguageManager.get_all_namespace_prefixes(self.lang_code)

            for link in wikicode.filter_wikilinks():
                link_text = str(link.title).strip()
                cleaned = self.clean_link(link_text)

                # Skip interlanguage links (format: xx:Article where xx is 2-3 letter language code)
                if ':' in cleaned:
                    prefix = cleaned.split(':', 1)[0]
                    if len(prefix) in [2, 3] and prefix.isalpha() and prefix != self.lang_code:
                        continue  # Skip interlanguage link

                # Skip links that start with namespace prefixes
                if cleaned and not any(cleaned.startswith(prefix) for prefix in skip_prefixes):
                    resolved = self.resolve_redirect(cleaned)
                    if resolved != page.title:  # Skip self-links
                        links.append(resolved)
        except Exception as e:
            self.log.error(f"Link extraction failed for {page.title}: {e}")

        return article_data, links

    def process_dump(self, dump_path, output_dir, max_articles=None):
        """Enhanced processing with full feature set."""
        last_id = 0  # Skip checkpoint for testing
        batch_num = 1

        articles_buffer = []
        links_buffer = []

        print(f"{YELLOW}[PROCESSING] Opening dump file: {dump_path}{RESET}")
        with bz2.open(dump_path, 'rt', encoding='utf-8') as f:
            dump = mwxml.Dump.from_file(f)

            for page in dump:
                # Memory check every 100 articles
                if self.articles_processed % 100 == 0:
                    mem_mb = self.check_memory()
                    if mem_mb > 2000:
                        self.log.warning(f"High memory: {mem_mb:.1f}MB")
                    elif self.articles_processed % 500 == 0:
                        self.log.info(f"Processed {self.articles_processed} articles, Memory: {mem_mb:.1f}MB")

                # Only process main namespace
                if page.namespace != 0:
                    continue

                for revision in page:
                    if not revision.text:
                        continue

                    result = self.process_article(page, revision)
                    if result:
                        article_data, links = result
                        articles_buffer.append(article_data)
                        for link in links:
                            links_buffer.append((page.title, link))

                    self.articles_processed += 1

                    # Write batch
                    if len(articles_buffer) >= self.batch_size:
                        self.write_batch(articles_buffer, links_buffer, batch_num, output_dir)
                        print(f"{GREEN}[SUCCESS] Batch {batch_num}: {len(articles_buffer)} articles{RESET}")
                        articles_buffer = []
                        links_buffer = []
                        batch_num += 1

                    if max_articles and self.articles_processed >= max_articles:
                        break

                if max_articles and self.articles_processed >= max_articles:
                    break

        # Write final batch
        if articles_buffer:
            self.write_batch(articles_buffer, links_buffer, batch_num, output_dir)
            print(f"{GREEN}[SUCCESS] Final batch {batch_num}: {len(articles_buffer)} articles{RESET}")

    def write_batch(self, articles, links, batch_num, output_dir):
        """Write batch to compressed files."""
        # Articles with enhanced data
        articles_file = output_dir / f"articles_batch_{batch_num:04d}.jsonl.gz"
        with gzip.open(articles_file, 'wt', encoding='utf-8') as f:
            for article in articles:
                f.write(json.dumps(article, ensure_ascii=False) + '\n')

        # Links
        links_file = output_dir / f"links_batch_{batch_num:04d}.csv.gz"
        with gzip.open(links_file, 'wt', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(links)

        # Checkpoint
        if articles:
            last_article_id = articles[-1]['id']
            self.save_checkpoint(last_article_id, batch_num)

def main():
    """Test enhanced parser with 1000 articles."""
    import argparse

    parser = argparse.ArgumentParser(description='Multi-Language Wikipedia Parser')
    parser.add_argument('--lang', type=str, default='pl',
                       help='Language code (e.g., pl, en) (default: pl)')
    parser.add_argument('--max-articles', type=int, default=1000,
                       help='Maximum articles to process (default: 1000)')

    args = parser.parse_args()

    # Get language configuration
    try:
        lang_config = LanguageManager.get_language_info(args.lang)
        dbname = LanguageManager.get_dbname(args.lang)
    except Exception as e:
        print(f"{RED}[ERROR] Failed to load configuration for language '{args.lang}': {e}{RESET}")
        return

    base_dir = Path('/mnt/c/Users/PC/WikiGraph')
    dump_path = base_dir / 'raw_data_wiki' / f'{dbname}-20251201-pages-articles-multistream.xml.bz2'
    output_dir = base_dir / f'processed_batches_{args.lang}'

    # Create language-specific output directory
    output_dir.mkdir(exist_ok=True)

    print(f"{GREEN}==> PHASE 1 ENHANCED PARSER - {lang_config['name']} ({lang_config['local_name']}) Test{RESET}")
    print("=" * 60)
    print(f"{BLUE}[LANG] Language: {lang_config['name']} ({args.lang}){RESET}")
    print(f"{BLUE}[FILE] Data source: {dump_path}{RESET}")
    print(f"{BLUE}[FILE] Output directory: {output_dir}{RESET}")
    print(f"{YELLOW}[CONFIG] Batch size: 500 articles{RESET}")
    print(f"{YELLOW}[CONFIG] Test limit: {args.max_articles:,} articles{RESET}")
    print("=" * 60)

    enhanced_parser = EnhancedParser(lang_code=args.lang)

    # Memory check
    initial_mem = enhanced_parser.check_memory()
    print(f"{BLUE}[MEMORY] Initial memory usage: {initial_mem:.1f}MB{RESET}")

    enhanced_parser.process_dump(dump_path, output_dir, max_articles=args.max_articles)

    # Final stats
    final_mem = enhanced_parser.check_memory()
    print(f"{BLUE}[MEMORY] Final memory usage: {final_mem:.1f}MB{RESET}")
    print(f"{BLUE}[MEMORY] Memory delta: {final_mem - initial_mem:.1f}MB{RESET}")

    enhanced_parser.save_redirects()

    print(f"\n{GREEN}[SUCCESS] Enhanced Parser Test Complete{RESET}")
    print(f"{BLUE}[STATS] Articles processed: {enhanced_parser.articles_processed:,}{RESET}")
    print(f"{BLUE}[STATS] Redirects found: {enhanced_parser.redirects_found:,}{RESET}")

if __name__ == "__main__":
    main()
