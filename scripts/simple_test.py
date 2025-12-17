#!/usr/bin/env python3
import time
import bz2

path = '/mnt/c/Users/PC/WikiGraph/raw_data_wiki/plwiki-20251201-pages-articles-multistream.xml.bz2'
print("Testing file read...")

start = time.time()
count = 0
total_chars = 0

with bz2.open(path, 'rt', encoding='utf-8', errors='ignore') as f:
    for i, line in enumerate(f):
        total_chars += len(line)
        if '<page>' in line:
            count += 1
        if count >= 100:
            break

elapsed = time.time() - start
print(f"Found {count} pages in {elapsed:.2f} seconds")
print(f"Read {total_chars:,} characters")
print(f"Speed: {count/elapsed:.1f} pages/second")
print(f"Read speed: {total_chars/elapsed/1024/1024:.2f} MB/sec")
