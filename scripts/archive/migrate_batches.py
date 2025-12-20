#!/usr/bin/env python3
"""
Migration Script: Add Language Field to Polish Batch Files

This script migrates existing Polish Wikipedia batch files to include
the "language": "pl" field required for multi-language database support.

INPUT:  ~/WikiGraph/processed_batches/articles_batch_*.jsonl.gz (1,054 files)
OUTPUT: ~/WikiGraph/processed_batches_pl/articles_batch_*.jsonl.gz

PROCESSING:
- Streaming line-by-line (memory efficient)
- Preserves all existing fields
- Adds "language": "pl" to each article
- Maintains gzip compression
- Progress logging every 10 files
"""

import gzip
import json
import sys
from pathlib import Path
from typing import List


def migrate_batch_file(input_file: Path, output_file: Path, language_code: str = 'pl') -> int:
    """
    Migrate a single batch file by adding language field to each article.

    Args:
        input_file: Path to input .jsonl.gz file
        output_file: Path to output .jsonl.gz file
        language_code: Language code to add (default: 'pl')

    Returns:
        Number of articles processed in this file
    """
    articles_count = 0

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        with gzip.open(input_file, 'rt', encoding='utf-8') as infile:
            with gzip.open(output_file, 'wt', encoding='utf-8') as outfile:
                for line in infile:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        # Parse JSON
                        article = json.loads(line)

                        # Add language field
                        article['language'] = language_code

                        # Write back with proper formatting
                        outfile.write(json.dumps(article, ensure_ascii=False) + '\n')
                        articles_count += 1

                    except json.JSONDecodeError as e:
                        print(f"WARNING: Skipping corrupted JSON in {input_file}: {e}")
                        continue

    except Exception as e:
        print(f"ERROR: Failed to process {input_file}: {e}")
        return 0

    return articles_count


def find_batch_files(input_dir: Path) -> List[Path]:
    """Find all articles_batch_*.jsonl.gz files in input directory."""
    pattern = "articles_batch_*.jsonl.gz"
    return sorted(list(input_dir.glob(pattern)))


def main():
    """Main migration execution."""
    print("=" * 70)
    print("POLISH WIKIPEDIA BATCH MIGRATION")
    print("Add 'language': 'pl' field to all articles")
    print("=" * 70)

    # Setup paths
    base_dir = Path('/mnt/c/Users/PC/WikiGraph')
    input_dir = base_dir / 'processed_batches'
    output_dir = base_dir / 'processed_batches_pl'

    print(f"Input directory:  {input_dir}")
    print(f"Output directory: {output_dir}")
    print()

    # Find all batch files
    batch_files = find_batch_files(input_dir)
    total_files = len(batch_files)

    if total_files == 0:
        print(f"ERROR: No batch files found in {input_dir}")
        sys.exit(1)

    print(f"Found {total_files} batch files to migrate")
    print()

    # Process files
    total_articles = 0
    processed_files = 0

    for i, input_file in enumerate(batch_files, 1):
        # Determine output file path
        relative_path = input_file.relative_to(input_dir)
        output_file = output_dir / relative_path

        # Migrate file
        articles_in_file = migrate_batch_file(input_file, output_file)

        if articles_in_file > 0:
            total_articles += articles_in_file
            processed_files += 1

            # Progress logging
            if i % 10 == 0 or i == total_files:
                print(f"Progress: {i}/{total_files} files | {total_articles:,} articles")

        else:
            print(f"WARNING: No articles processed in {input_file}")

    # Final summary
    print()
    print("=" * 70)
    print("MIGRATION COMPLETE")
    print("=" * 70)
    print(f"Files processed: {processed_files}/{total_files}")
    print(f"Total articles:  {total_articles:,}")
    print(f"Output location: {output_dir}")
    print()

    # Verification
    output_files = find_batch_files(output_dir)
    if len(output_files) == processed_files:
        print("✅ SUCCESS: All files migrated successfully")
        print("✅ Ready for multi-language database loading")
    else:
        print(f"⚠️  WARNING: Expected {processed_files} output files, found {len(output_files)}")

    # Sample verification
    if output_files:
        sample_file = output_files[0]
        try:
            with gzip.open(sample_file, 'rt', encoding='utf-8') as f:
                first_line = f.readline().strip()
                sample_article = json.loads(first_line)

            if 'language' in sample_article and sample_article['language'] == 'pl':
                print("✅ VERIFIED: Language field correctly added")
                print(f"   Sample: {sample_article.get('title', 'Unknown')} has language='{sample_article['language']}'")
            else:
                print("❌ ERROR: Language field not found in sample")
        except Exception as e:
            print(f"❌ ERROR: Could not verify sample file: {e}")


if __name__ == "__main__":
    main()
