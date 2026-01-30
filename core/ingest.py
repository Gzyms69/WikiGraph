#!/usr/bin/env python3
"""
WikiGraph Master Ingestion Orchestrator
Automates the Offline Phase of the pipeline: Download -> SQLite Load -> Infobox Extraction -> CSV Generation
"""

import sys
import argparse
import subprocess
import time
from pathlib import Path

def run_step(description, cmd_args):
    print(f"\n🚀 STEP: {description}")
    start = time.time()
    try:
        subprocess.run([sys.executable] + cmd_args, check=True)
        print(f"✅ Completed in {time.time() - start:.1f}s")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="WikiGraph Ingestion Pipeline (Offline Phase)")
    parser.add_argument("--lang", required=True, help="Language code (e.g. de, pl)")
    parser.add_argument("--limit", type=int, default=0, help="Limit rows/articles for testing (0=no limit)")
    parser.add_argument("--download", action="store_true", help="Download dumps first")
    parser.add_argument("--skip-sql", action="store_true", help="Skip SQLite schema/SQL load")
    parser.add_argument("--skip-infobox", action="store_true", help="Skip XML infobox extraction")
    parser.add_argument("--skip-csv", action="store_true", help="Skip Neo4j CSV generation")
    args = parser.parse_args()

    lang = args.lang
    limit_arg = str(args.limit)
    print(f"🌍 Starting Ingestion Pipeline for [{lang.upper()}] (Limit: {args.limit})")

    # 1. Download
    if args.download:
        run_step("Download Dumps", ["core/tools/fetch_sql_dumps.py", lang])

    # 2. SQLite SQL Load
    if not args.skip_sql:
        cmd = ["core/sqlite_loader.py", "--lang", lang, "--init"]
        if args.limit > 0:
            cmd.extend(["--limit", limit_arg])
        run_step("Initialize SQLite & Load SQL Dumps", cmd)

    # 3. Infobox Extraction
    if not args.skip_infobox:
        # extract_infoboxes accepts 0 as 'no limit'
        run_step("Extract Infoboxes from XML", ["core/tools/extract_infoboxes.py", "--lang", lang, "--limit", limit_arg])

    # 4. CSV Generation
    if not args.skip_csv:
        cmd = ["core/tools/prepare_neo4j_csv.py", "--lang", lang]
        if args.limit > 0:
            cmd.extend(["--limit", limit_arg])
        run_step("Generate Neo4j CSVs", cmd)

    print("\n✨ OFFLINE PIPELINE COMPLETE.")
    print(f"   Next Steps:")
    print(f"   1. Stop Neo4j:   docker stop neo4j-{lang}")
    print(f"   2. Import Data:  bash core/tools/run_neo4j_import.sh {lang}")
    print(f"   3. Start Neo4j:  docker start neo4j-{lang}")
    print(f"   4. Post-Process: python3 tools/compute_edge_degrees.py --lang {lang}")

if __name__ == "__main__":
    main()