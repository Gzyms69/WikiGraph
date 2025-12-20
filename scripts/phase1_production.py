#!/usr/bin/env python3
"""
PHASE 1: PRODUCTION PARSER - Full Wikipedia Dump Processing
Optimized for speed and safety with 2000 article batches.
Based on successful memory tests (44MB for 1000 articles).
"""

import sys
from pathlib import Path
import json
from datetime import datetime

# Add the parent directory to path to import our parser
sys.path.append(str(Path(__file__).parent))

from phase1_enhanced import EnhancedParser

# ANSI color codes for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

class ProductionParser(EnhancedParser):
    """Production parser optimized for full dump processing."""

    def __init__(self):
        super().__init__()
        self.batch_size = 2000  # Optimized for speed (tested safe at 44MB/1000 articles)
        self.checkpoint_interval = 10000  # Save checkpoint every 10K articles

    def run_full_dump(self):
        """Process entire Wikipedia dump with production settings."""
        print("="*70)
        print("POLISH WIKIPEDIA - FULL PRODUCTION PROCESSING")
        print("="*70)
        print(f"Batch size: {self.batch_size:,} articles")
        print(f"Estimated total articles: ~2,000,000")
        print(f"Estimated total links: ~180,000,000")
        print(f"Estimated batches: ~1,000")
        print(f"Estimated time: 3-4 hours")
        print(f"Memory limit: 19GB (WSL)")
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
            dump_path = Path('/mnt/c/Users/PC/WikiGraph/raw_data_wiki/plwiki-20251201-pages-articles-multistream.xml.bz2')
            self.process_dump(dump_path, self.output_dir, max_articles=None)  # Process all

            # Final statistics
            end_time = datetime.now()
            duration = end_time - start_time

            print(f"\n{GREEN}{'='*70}{RESET}")
            print(f"{GREEN}PROCESSING COMPLETE!{RESET}")
            print(f"{'='*70}{RESET}")
            print(f"Duration: {duration}")
            print(f"Articles processed: {self.articles_processed:,}")
            print(f"Redirects found: {self.redirects_found:,}")
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

def main():
    """Production parser entry point."""
    base_dir = Path('/mnt/c/Users/PC/WikiGraph')
    dump_path = base_dir / 'raw_data_wiki' / 'plwiki-20251201-pages-articles-multistream.xml.bz2'

    if not dump_path.exists():
        print(f"{RED}[ERROR] Dump file not found: {dump_path}{RESET}")
        sys.exit(1)

    # Set output directory before creating parser
    output_dir = base_dir / 'processed_batches'
    output_dir.mkdir(exist_ok=True)

    parser = ProductionParser()
    # Set the output directory manually since it's not in __init__
    parser.output_dir = output_dir
    parser.run_full_dump()

if __name__ == "__main__":
    main()
