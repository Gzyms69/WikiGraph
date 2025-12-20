#!/usr/bin/env python3
"""
Migrate Links Files: Add Language Field

Adds language field to existing Polish Wikipedia links files.

INPUT:  ~/WikiGraph/processed_batches/links_batch_*.csv.gz
        Format: source_title,target_title

OUTPUT: ~/WikiGraph/processed_batches_pl/links_batch_*.csv.gz
        Format: source_title,target_title,pl
"""

import gzip
import csv
import sys
from pathlib import Path


def migrate_links_file(input_file: Path, output_file: Path, language_code: str = 'pl') -> int:
    """
    Migrate a single links file by adding language field.

    Args:
        input_file: Path to input .csv.gz file
        output_file: Path to output .csv.gz file
        language_code: Language code to add (default: 'pl')

    Returns:
        Number of links processed in this file
    """
    links_count = 0

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        with gzip.open(input_file, 'rt', encoding='utf-8', newline='') as infile:
            with gzip.open(output_file, 'wt', encoding='utf-8', newline='') as outfile:
                reader = csv.reader(infile)
                writer = csv.writer(outfile)

                for row in reader:
                    if len(row) == 2:  # source_title, target_title
                        # Add language field: source_title, target_title, language
                        writer.writerow([row[0], row[1], language_code])
                        links_count += 1
                    else:
                        # Skip malformed rows
                        continue

    except Exception as e:
        print(f"ERROR: Failed to process {input_file}: {e}")
        return 0

    return links_count


def find_links_files(input_dir: Path) -> list[Path]:
    """Find all links_batch_*.csv.gz files in input directory."""
    pattern = "links_batch_*.csv.gz"
    return sorted(list(input_dir.glob(pattern)))


def main():
    """Main migration execution."""
    print("=" * 70)
    print("POLISH WIKIPEDIA LINKS MIGRATION")
    print("Add 'language' field to all links")
    print("=" * 70)

    # Setup paths
    base_dir = Path('/mnt/c/Users/PC/WikiGraph')
    input_dir = base_dir / 'processed_batches'
    output_dir = base_dir / 'processed_batches_pl'

    print(f"Input directory:  {input_dir}")
    print(f"Output directory: {output_dir}")
    print()

    # Find all links files
    links_files = find_links_files(input_dir)
    total_files = len(links_files)

    if total_files == 0:
        print(f"ERROR: No links files found in {input_dir}")
        sys.exit(1)

    print(f"Found {total_files} links files to migrate")
    print()

    # Process files
    total_links = 0
    processed_files = 0

    for i, input_file in enumerate(links_files, 1):
        # Determine output file path
        relative_path = input_file.relative_to(input_dir)
        output_file = output_dir / relative_path

        # Migrate file
        links_in_file = migrate_links_file(input_file, output_file)

        if links_in_file > 0:
            total_links += links_in_file
            processed_files += 1

            # Progress logging
            if i % 10 == 0 or i == total_files:
                print(f"Progress: {i}/{total_files} files | {total_links:,} links")

        else:
            print(f"WARNING: No links processed in {input_file}")

    # Final summary
    print()
    print("=" * 70)
    print("LINKS MIGRATION COMPLETE")
    print("=" * 70)
    print(f"Files processed: {processed_files}/{total_files}")
    print(f"Total links:  {total_links:,}")
    print(f"Output location: {output_dir}")
    print()

    # Verification
    output_files = find_links_files(output_dir)
    if len(output_files) == processed_files:
        print("✅ SUCCESS: All links files migrated successfully")
        print("✅ Language field added to all link records")
    else:
        print(f"⚠️  WARNING: Expected {processed_files} output files, found {len(output_files)}")

    # Sample verification
    if output_files:
        sample_file = output_files[0]
        try:
            with gzip.open(sample_file, 'rt', encoding='utf-8', newline='') as f:
                reader = csv.reader(f)
                first_row = next(reader)

            if len(first_row) == 3 and first_row[2] == 'pl':
                print("✅ VERIFIED: Language field correctly added")
                print(f"   Sample: {first_row[0]} → {first_row[1]} (lang: {first_row[2]})")
            else:
                print("❌ ERROR: Language field not found in sample")
        except Exception as e:
            print(f"❌ ERROR: Could not verify sample file: {e}")


if __name__ == "__main__":
    main()
