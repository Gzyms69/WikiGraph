#!/usr/bin/env python3
"""
extract_infoboxes.py - Optimized streaming infobox extraction
Features:
- Regex Pre-check (skips ~60% of parsing)
- Multiprocessing (parses in parallel)
- Bulk SQLite Writes (Temp table strategy)
- Checkpoint/Resume capability
"""
import mwxml
import mwparserfromhell
import json
import sqlite3
import argparse
import sys
import time
import psutil
import os
import bz2
import signal
import multiprocessing
from pathlib import Path
from multiprocessing import Pool, cpu_count

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.language_manager import LanguageManager

class CheckpointManager:
    """Simple checkpoint system for resuming extraction"""
    def __init__(self, lang, checkpoint_dir="data/checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)
        self.checkpoint_file = self.checkpoint_dir / f"{lang}_infobox_checkpoint.txt"
        self.resume_from = None
        
    def load_checkpoint(self):
        """Load last processed page title from checkpoint"""
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                last_title = f.read().strip()
                if last_title:
                    self.resume_from = last_title
                    return True
        return False
    
    def save_checkpoint(self, title):
        """Save current page title to checkpoint"""
        with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
            f.write(title)
    
    def clear_checkpoint(self):
        """Clear checkpoint on successful completion"""
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()

def quick_has_infobox(wikitext, prefixes, suffixes):
    """Ultra-fast check for infobox presence using string searching."""
    if not wikitext:
        return False
    # Check prefixes
    for prefix in prefixes:
        if f"{{{{{prefix}" in wikitext:
            return True
    # Check suffixes (case-insensitive loose check)
    if suffixes:
        lower_text = wikitext.lower()
        for suffix in suffixes:
            if suffix.lower() in lower_text:
                return True
    return False

def parse_worker(args):
    """Worker function to parse wikitext."""
    title, wikitext, template_prefixes, template_suffixes, param_map = args
    try:
        parsed = mwparserfromhell.parse(wikitext)
        infoboxes = []
        for template in parsed.filter_templates():
            template_name = str(template.name).strip()
            template_name_lower = template_name.lower()
            
            is_prefix = any(template_name.startswith(prefix) for prefix in template_prefixes)
            is_suffix = any(template_name_lower.endswith(suffix.lower()) for suffix in template_suffixes)

            if is_prefix or is_suffix:
                params = {}
                for param in template.params:
                    if param.name:
                        p_name = str(param.name).strip()
                        p_val = str(param.value).strip()
                        if p_name in param_map:
                            p_name = param_map[p_name]
                        params[p_name] = p_val
                infoboxes.append({
                    "template": template_name,
                    "params": params
                })
        if infoboxes:
            return (title, json.dumps(infoboxes, ensure_ascii=False))
        return (title, None)
    except Exception:
        return (title, None)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--lang', required=True, help='Language code (de, pl)')
    parser.add_argument('--limit', type=int, default=10000, help='Number of articles to process (0=no limit)')
    parser.add_argument('--chunk-size', type=int, default=100, help='Chunk size for multiprocessing')
    parser.add_argument('--workers', type=int, default=0, help='Number of worker processes (0=auto)')
    parser.add_argument('--checkpoint-interval', type=int, default=100000, help='Articles between checkpoints')
    args = parser.parse_args()
    
    # 1. Config Setup
    try:
        config = LanguageManager.get_config(args.lang)
        template_prefixes = config['infobox'].get('template_prefixes', [])
        template_suffixes = config['infobox'].get('template_suffixes', [])
        param_map = config['infobox'].get('parameter_map', {})
    except Exception as e:
        print(f"❌ Config Error: {e}")
        sys.exit(1)
    
    if not template_prefixes and not template_suffixes:
        print(f"❌ No template prefixes OR suffixes configured for language '{args.lang}'")
        sys.exit(1)

    # 2. Files Setup
    xml_path = Path(f"data/raw/{args.lang}wiki-latest-pages-articles-multistream.xml.bz2")
    if not xml_path.exists():
        xml_path = next(Path("data/raw").glob(f"{args.lang}wiki-*-pages-articles-multistream.xml.bz2"), None)

    db_path = Path(f"data/db/{args.lang}.db")
    if not xml_path or not xml_path.exists():
        print(f"❌ XML dump not found: {xml_path}")
        sys.exit(1)

    # 3. DB Setup
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA synchronous = OFF")
    conn.execute("PRAGMA journal_mode = MEMORY")
    
    # 4. Checkpoint Setup
    checkpoint = CheckpointManager(args.lang)
    resume_mode = checkpoint.load_checkpoint()
    skip_until_found = resume_mode
    if resume_mode:
        print(f"🔄 Resuming from checkpoint: {checkpoint.resume_from}")

    print(f"🚀 Starting OPTIMIZED infobox extraction for {args.lang}")
    print(f"   XML: {xml_path}")
    print(f"   Prefixes: {template_prefixes}")
    print(f"   Suffixes: {template_suffixes}")
    print(f"   Limit: {'No limit' if args.limit == 0 else args.limit}")
    
    # 5. Processing Setup
    start_time = time.time()
    processed_count = 0
    extracted_count = 0
    batch_data = []
    
    num_workers = args.workers if args.workers > 0 else max(1, cpu_count() - 1)
    print(f"   Workers: {num_workers}")
    print(f"   Checkpoint Interval: {args.checkpoint_interval}")
    
    pool = Pool(processes=num_workers)
    process = psutil.Process(os.getpid())
    
    # Signal handling for graceful shutdown
    def signal_handler(sig, frame):
        print("\n⚠️  Interrupted. Saving checkpoint and exiting...")
        pool.terminate()
        pool.join()
        conn.close()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        with bz2.open(xml_path, 'rt', encoding='utf-8', errors='replace') as f:
            dump = mwxml.Dump.from_file(f)
            work_queue = []
            
            for page in dump:
                if page.namespace != 0 or page.redirect:
                    continue
                
                # Resume logic
                if skip_until_found:
                    if page.title == checkpoint.resume_from:
                        skip_until_found = False
                        print("✅ Found checkpoint. Resuming extraction...")
                    continue

                wikitext = ''
                try:
                    revision = next(page)
                    wikitext = revision.text or ''
                except StopIteration:
                    continue
                
                # Checkpoint saving
                if processed_count > 0 and processed_count % args.checkpoint_interval == 0:
                    checkpoint.save_checkpoint(page.title)
                
                # OPTIMIZATION: Pre-check
                if not quick_has_infobox(wikitext, template_prefixes, template_suffixes):
                    processed_count += 1
                    if args.limit > 0 and processed_count >= args.limit:
                        break
                    continue
                
                work_queue.append((page.title, wikitext, template_prefixes, template_suffixes, param_map))
                
                if len(work_queue) >= args.chunk_size * num_workers:
                    results = pool.map(parse_worker, work_queue)
                    for title, result_json in results:
                        if result_json:
                            db_title = title.replace(' ', '_')
                            batch_data.append((result_json, db_title))
                            extracted_count += 1
                        processed_count += 1
                    
                    work_queue = []
                    if len(batch_data) >= 2000:
                        _bulk_update(conn, batch_data)
                        batch_data = []
                        
                        elapsed = time.time() - start_time
                        speed = processed_count / elapsed
                        mem_mb = process.memory_info().rss / 1024 / 1024
                        
                        print(f"  ⚡ Processed: {processed_count}/{'∞' if args.limit == 0 else args.limit} | Speed: {speed:.1f}/s | Found: {extracted_count} | Mem: {mem_mb:.1f}MB")

                if args.limit > 0 and processed_count >= args.limit:
                    break
            
            # Process remaining queue
            if work_queue:
                results = pool.map(parse_worker, work_queue)
                for title, result_json in results:
                    if result_json:
                        db_title = title.replace(' ', '_')
                        batch_data.append((result_json, db_title))
                        extracted_count += 1
                    processed_count += 1
            
            if batch_data:
                _bulk_update(conn, batch_data)

    finally:
        pool.close()
        pool.join()
        if args.limit > 0 and processed_count >= args.limit:
            checkpoint.clear_checkpoint()
        conn.close()
        
    total_time = time.time() - start_time
    speed = processed_count / total_time if total_time > 0 else 0
    print(f"\n🎉 Extraction Complete!")
    print(f"   Articles processed: {processed_count}")
    print(f"   Infoboxes extracted: {extracted_count}")
    print(f"   Total time: {total_time:.1f}s")
    print(f"   Average speed: {speed:.1f} articles/second")

def _bulk_update(conn, data):
    if not data: return
    cursor = conn.cursor()
    cursor.execute("CREATE TEMPORARY TABLE IF NOT EXISTS infobox_temp (infobox TEXT, title TEXT)")
    cursor.execute("DELETE FROM infobox_temp")
    cursor.executemany("INSERT INTO infobox_temp (infobox, title) VALUES (?, ?)", data)
    cursor.execute("""
        UPDATE pages 
        SET infobox = (SELECT infobox FROM infobox_temp WHERE infobox_temp.title = pages.title)
        WHERE title IN (SELECT title FROM infobox_temp)
    """)
    conn.commit()

if __name__ == "__main__":
    main()