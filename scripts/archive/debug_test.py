#!/usr/bin/env python3
import re
import bz2

path = '/mnt/c/Users/PC/WikiGraph/raw_data_wiki/plwiki-20251201-pages-articles-multistream.xml.bz2'

with bz2.open(path, 'rt', encoding='utf-8', errors='ignore') as f:
    content = ""
    page_count = 0
    
    for line in f:
        content += line
        if '</page>' in line:
            page_count += 1
            
            # Try different regex patterns
            title_match = re.search(r'<title>(.*?)</title>', content)
            if title_match:
                print(f"\nPage {page_count}: {title_match.group(1)}")
            
            # Pattern 1: Standard
            text_match1 = re.search(r'<text[^>]*>(.*?)</text>', content, re.DOTALL)
            if text_match1:
                print(f"  Pattern 1 found text: {len(text_match1.group(1))} chars")
            else:
                print(f"  Pattern 1: NO TEXT FOUND")
            
            # Pattern 2: More flexible
            text_match2 = re.search(r'<text[^>]*>([\s\S]*?)</text>', content)
            if text_match2:
                print(f"  Pattern 2 found text: {len(text_match2.group(1))} chars")
            
            # Show a snippet of the content around <text>
            text_pos = content.find('<text')
            if text_pos != -1:
                snippet = content[max(0, text_pos-100):min(len(content), text_pos+200)]
                print(f"  Text tag context: {snippet}")
            
            content = ""
            
            if page_count >= 3:
                break
