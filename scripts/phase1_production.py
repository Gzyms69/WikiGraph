#!/usr/bin/env python3
"""
PHASE 1: PRODUCTION PARSER - Full Wikipedia Dump Processing
Optimized for speed and safety with 2000 article batches.
Based on successful memory tests (44MB for 1000 articles).
"""

import sys
import argparse
import glob
from pathlib import Path
import json
from datetime import datetime

# Add the parent directory to path to import our parser
sys.path.append(str(Path(__file__).parent))

from phase1_enhanced import EnhancedParser
from config.language_manager import LanguageManager

# ANSI color codes for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

class ProductionParser(EnhancedParser):
    """Production parser optimized for full dump processing."""

    def __init__(self, lang_code='pl', output_dir=None):
        super().__init__(lang_code=lang_code)
        self.batch_size = 20000  # Increased for English Wiki (avoids 10k+ small files)
        self.checkpoint_interval = 20000  # Save checkpoint every batch
        
        # Override output dir if provided
        if output_dir:
            self.output_dir = output_dir

    def run_full_dump(self, dump_path):
        """Process entire Wikipedia dump with production settings."""
        lang_name = LanguageManager.get_language_info(self.lang_code)['name'].upper()
        
        print("="*70)
        print(f"{lang_name} WIKIPEDIA - FULL PRODUCTION PROCESSING")
        print("="*70)
        print(f"Batch size: {self.batch_size:,} articles")
        # Estimates are rough; could be made language-specific if needed
        print(f"Estimated time: Depends on dump size")
        print(f"Memory limit: 19GB (WSL)")
        print(f"Dump file: {dump_path}")
        print(f"Output directory: {self.output_dir}")
        print("="*70)

        # Ask for confirmation
        response = input("\nStart full processing? (yes/NO): ").strip().lower()
        if response != 'yes':
            print("Aborted by user.")
            return

        print("\nStarting processing at full speed...")
        print("Press Ctrl+C to pause (checkpoint will be saved)")
        print("-" * 70)

        start_time = datetime.now()

        try:
            self.process_dump(dump_path, self.output_dir, max_articles=None)  # Process all

            # Final statistics
            end_time = datetime.now()
            duration = end_time - start_time

            print(f"\n{GREEN}{'='*70}{RESET}")
            print(f"{GREEN}PROCESSING COMPLETE!{RESET}")
            print(f"{RESET}{'='*70}{RESET}")
            print(f"Duration: {duration}")
            print(f"Articles processed: {self.articles_processed:,}")
            print(f"Redirects found: {self.redirects_found:,}")
            # Use glob on the specific output directory
            print(f"Batches created: {len(list(self.output_dir.glob('articles_batch_*.jsonl.gz')))}")
            print(f"Peak memory: {self.check_memory():.1f}MB")
            print(f"Output location: {self.output_dir}")

        except KeyboardInterrupt:
            print(f"\n\n{YELLOW}[INTERRUPTED] Processing paused by user.{RESET}")
            print(f"{BLUE}[CHECKPOINT] Progress saved. Resume with same command.{RESET}")
            sys.exit(0)
        except Exception as e:
            print(f"\n{RED}[FATAL ERROR] {e}{RESET}")
            sys.exit(1)

def find_dump_file(base_dir, lang_code):
    """Find the latest dump file for the given language."""
    try:
        dbname = LanguageManager.get_dbname(lang_code)
    except Exception:
        # Fallback if config fails, though get_dbname should raise
        dbname = f"{lang_code}wiki"

    raw_dir = base_dir / 'raw_data_wiki'
    pattern = f"{dbname}-*-pages-articles-multistream.xml.bz2"
    
    files = sorted(raw_dir.glob(pattern), reverse=True)
    
    if not files:
        return None
    
    return files[0]

def main():
    """Production parser entry point."""
    parser = argparse.ArgumentParser(description='WikiGraph Production Parser')
    parser.add_argument('--lang', type=str, default='pl',
                       help='Language code (e.g., pl, en) (default: pl)')
    
    args = parser.parse_args()
    
    # Validate language
    try:
        LanguageManager.get_language_info(args.lang)
    except Exception as e:
        print(f"{RED}[ERROR] Invalid language '{args.lang}': {e}{RESET}")
        sys.exit(1)

    base_dir = Path('/mnt/c/Users/PC/WikiGraph')
    
    # Find dump file
    dump_path = find_dump_file(base_dir, args.lang)
    if not dump_path or not dump_path.exists():
        # Try finding generic pattern if specific dbname not found
        fallback_pattern = f"{args.lang}wiki-*-pages-articles-multistream.xml.bz2"
        files = sorted((base_dir / 'raw_data_wiki').glob(fallback_pattern), reverse=True)
        if files:
            dump_path = files[0]
        else:
            print(f"{RED}[ERROR] Dump file not found for language '{args.lang}' in {base_dir / 'raw_data_wiki'}{RESET}")
            print(f"Expected pattern: {LanguageManager.get_dbname(args.lang)}-*-pages-articles-multistream.xml.bz2")
            sys.exit(1)

    # Set output directory
    output_dir = base_dir / f'processed_batches_{args.lang}'
    output_dir.mkdir(exist_ok=True)

    # Initialize and run
    parser = ProductionParser(lang_code=args.lang, output_dir=output_dir)
    parser.run_full_dump(dump_path)

if __name__ == "__main__":
    main()