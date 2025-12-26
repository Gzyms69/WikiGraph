#!/usr/bin/env python3
"""
CORE: PARSER
- High Performance: Parallel wikitext parsing using lxml.
- Instant Resume: Seeks directly to byte offset via Index.
- Stability: Direct-to-disk redirect streaming.
"""

import os
import sys
import json
import gzip
import csv
import re
import argparse
import gc
from pathlib import Path
from multiprocessing import Pool, cpu_count
from lxml import etree
import rapidgzip
from tqdm import tqdm

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))
from config.language_manager import LanguageManager

def worker_init(lang_code):
    global category_prefixes, redirect_keywords, worker_lang
    worker_lang = lang_code
    category_prefixes = LanguageManager.get_namespace_prefixes(lang_code).get('category', ['Category:'])
    redirect_keywords = LanguageManager.get_redirect_keywords(lang_code)

def parse_page_xml(page_xml):
    """Worker: Parses raw XML bytes into structured data."""
    try:
        ns = "{http://www.mediawiki.org/xml/export-0.11/}"
        elem = etree.fromstring(page_xml)
        if elem.findtext(f"{ns}ns") != '0': return None
        
        title = elem.findtext(f"{ns}title")
        page_id = elem.findtext(f"{ns}id")
        rev = elem.find(f"{ns}revision")
        if rev is None: return None
        text = rev.findtext(f"{ns}text")
        if not text: return None
        
        # Redirect Check
        is_redir = any(f"#{kw.lower()}" in text[:300].lower() for kw in redirect_keywords)
        if is_redir:
            match = re.search(r'\[\[([^\]|]+)', text, re.IGNORECASE)
            target = match.group(1).strip() if match else None
            return ('redirect', (title, target))

        # Metadata
        prefix_pattern = '|'.join(re.escape(p.rstrip(':')) for p in category_prefixes)
        categories = [c.strip() for c in re.findall(rf'\[\[\s*(?:{{prefix_pattern}})\s*:\s*([^\]|]+)', text, re.IGNORECASE)]
        
        clean_text = re.sub(r'\{\{.*?\}\}', '', text, flags=re.DOTALL)
        clean_text = re.sub(r'\[\[(?:[^\|]*\|)?([^\|]+)\]\]', r'\1', clean_text)
        word_count = len(clean_text.split())

        article_data = {
            'id': int(page_id),
            'title': title,
            'language': worker_lang,
            'revision_id': int(rev.findtext(f"{ns}id")),
            'timestamp': rev.findtext(f"{ns}timestamp"),
            'word_count': word_count,
            'text_length': len(text),
            'categories': categories
        }
        
        links = re.findall(r'\[\[([^\]|#:]+)(?:\||\||\]\])', text)
        return ('article', (article_data, [l.strip() for l in links if l.strip()]))
    except:
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--lang', required=True)
    parser.add_argument('--batch-size', type=int, default=20000)
    parser.add_argument('--offset', type=int, default=0, help="Seek to byte offset")
    parser.add_argument('--total', type=int, default=0, help="Expected total for pbar")
    args = parser.parse_args()

    base_dir = Path(__file__).parent.parent
    dbname = LanguageManager.get_dbname(args.lang)
    
    # New Standard Paths
    dump_path = next((base_dir / 'data' / 'raw').glob(f'{dbname}-*-pages-articles-multistream.xml.bz2'))
    output_dir = base_dir / 'data' / 'processed' / args.lang
    output_dir.mkdir(exist_ok=True, parents=True)

    # Estimate total from index if not provided
    if args.total == 0:
        index_path = next((base_dir / 'data' / 'raw').glob(f'{dbname}-*-pages-articles-multistream-index.txt.bz2'))
        with bz2.open(index_path, 'rb') as f_idx:
            args.total = sum(1 for _ in f_idx)

    print(f"🚀 WikiGraph Parser [{args.lang.upper()}]")
    print(f"Input: {dump_path.name} | Output: {output_dir}")

    pool = Pool(processes=cpu_count(), initializer=worker_init, initargs=(args.lang,))
    
    articles_buffer, links_buffer, batch_num = [], [], 1
    redirect_file = output_dir / 'redirects_verified.csv'

    def page_generator(f):
        PAGE_START, PAGE_END = b'<page>', b'</page>'
        buffer = b""
        while True:
            chunk = f.read(4 * 1024 * 1024)
            if not chunk: break
            buffer += chunk
            while True:
                s, e = buffer.find(PAGE_START), buffer.find(PAGE_END)
                if s != -1 and e != -1 and e > s:
                    yield buffer[s:e+7].replace(b'<page>', b'<page xmlns="http://www.mediawiki.org/xml/export-0.11/">')
                    buffer = buffer[e+7:]
                else: break
            if len(buffer) > 20 * 1024 * 1024: buffer = b""

    with open(dump_path, 'rb') as f_raw:
        if args.offset > 0: f_raw.seek(args.offset)
        with rapidgzip.open(f_raw, parallelization=4) as f:
            with open(redirect_file, 'a', encoding='utf-8') as rf:
                redir_writer = csv.writer(rf)
                pbar = tqdm(total=args.total, desc=f"Parsing {args.lang.upper()}")
                
                for result in pool.imap_unordered(parse_page_xml, page_generator(f), chunksize=100):
                    pbar.update(1)
                    if not result: continue
                    res_type, data = result
                    if res_type == 'redirect':
                        redir_writer.writerow(data)
                    else:
                        articles_buffer.append(data[0])
                        for l in data[1]: links_buffer.append((data[0]['title'], l))
                        
                        if len(articles_buffer) >= args.batch_size:
                            with gzip.open(output_dir / f"articles_batch_{batch_num:04d}.jsonl.gz", 'wt') as af:
                                for a in articles_buffer: af.write(json.dumps(a, ensure_ascii=False) + '\n')
                            with gzip.open(output_dir / f"links_batch_{batch_num:04d}.csv.gz", 'wt') as lf:
                                csv.writer(lf).writerows([(l[0], l[1], args.lang) for l in links_buffer])
                            articles_buffer, links_buffer, batch_num = [], [], batch_num + 1
                            gc.collect()
                pbar.close()

    if articles_buffer:
        with gzip.open(output_dir / f"articles_batch_{batch_num:04d}.jsonl.gz", 'wt') as af:
            for a in articles_buffer: af.write(json.dumps(a, ensure_ascii=False) + '\n')
        with gzip.open(output_dir / f"links_batch_{batch_num:04d}.csv.gz", 'wt') as lf:
            csv.writer(lf).writerows([(l[0], l[1], args.lang) for l in links_buffer])

    pool.close(); pool.join()
    print("\n✅ Parsing Complete.")

import bz2
if __name__ == "__main__":
    main()