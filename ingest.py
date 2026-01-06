#!/usr/bin/env python3
"""
Universal Ingestion Controller for WikiGraph
Orchestrates the pipeline: Raw Dump -> Parser -> Graph Engine -> Neo4j
"""

import sys
import logging
import subprocess
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def check_processed_data(lang):
    """Check if parsed JSONL/CSV files exist for the language."""
    processed_dir = Path(f"data/processed/{lang}")
    if not processed_dir.exists():
        return False
    
    # Check for at least one batch
    articles = list(processed_dir.glob("articles_batch_*.jsonl.gz"))
    return len(articles) > 0

def run_parser(lang):
    """Run the parser to generate intermediate files."""
    logging.info(f"⚙️  Running Parser for {lang.upper()}...")
    cmd = [sys.executable, "core/parser.py", "--lang", lang]
    try:
        subprocess.run(cmd, check=True)
        logging.info(f"✅ Parser completed for {lang}.")
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Parser failed: {e}")
        sys.exit(1)

def run_ingestion(lang):
    """Run the Graph Engine to load data into Neo4j."""
    logging.info(f"🚀 Starting Neo4j Ingestion for {lang.upper()}...")
    
    from core.engine.graph_engine import WikiGraphEngine
    
    engine = WikiGraphEngine(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="wikigraph",
        max_connections=40
    )
    
    data_dir = f"data/processed/{lang}"
    engine.ingest_language(
        lang=lang,
        data_dir=data_dir,
        batch_size=5000,
        workers=16
    )

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 ingest.py <lang_code> [lang_code ...]")
        print("Example: python3 ingest.py pl de")
        sys.exit(1)
        
    languages = sys.argv[1:]
    
    for lang in languages:
        logging.info("="*60)
        logging.info(f"🌍 PROCESSING LANGUAGE: {lang.upper()}")
        logging.info("="*60)
        
        # 1. Parse (if needed)
        if not check_processed_data(lang):
            logging.warning(f"⚠️  Processed data not found for {lang}. invoking parser...")
            run_parser(lang)
        else:
            logging.info(f"✅ Found existing processed data for {lang}. Skipping parser.")
            
        # 2. Ingest
        run_ingestion(lang)
        
        logging.info(f"✨ Language {lang.upper()} processing complete.\n")

if __name__ == "__main__":
    main()
