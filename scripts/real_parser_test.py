#!/usr/bin/env python3
"""
REAL PARSER TEST - Actually processing content with timing
"""

import sys
import time
try:
    import psutil
    psutil_available = True
except ImportError:
    psutil = None
    psutil_available = False
import bz2
import re
import json
from pathlib import Path
from datetime import datetime

def main():
    print("🔍 REAL PARSER PERFORMANCE TEST")
    print("=" * 60)
    
    xml_path = Path("/mnt/c/Users/PC/WikiGraph/raw_data_wiki/plwiki-20251201-pages-articles-multistream.xml.bz2")
    
    if not xml_path.exists():
        print(f"❌ File not found: {xml_path}")
        return False
    
    print(f"📁 File: {xml_path.name}")
    print(f"📊 Size: {xml_path.stat().st_size / 1024**3:.2f} GB")
    ram_msg = f"💾 RAM available: {psutil.virtual_memory().available / 1024**3:.1f} GB\n" if psutil_available else "💾 RAM available: unknown\n"
    print(ram_msg)
    
    stats = {
        "pages_found": 0,
        "main_namespace": 0,
        "total_chars_read": 0,
        "start_time": time.time(),
        "peak_memory_mb": 0
    }
    
    sample_articles = []
    
    try:
        print("⏳ Opening file and processing ACTUAL content...")
        
        with bz2.open(xml_path, 'rt', encoding='utf-8', errors='ignore') as f:
            in_page = False
            page_content = ""
            title = None
            ns = None
            
            for line in f:
                # Update memory
                if psutil_available:
                    mem_mb = psutil.Process().memory_info().rss / 1024 / 1024
                    stats["peak_memory_mb"] = max(stats["peak_memory_mb"], mem_mb)
                stats["total_chars_read"] += len(line)
                
                if '<page>' in line:
                    in_page = True
                    page_content = ""
                    title = None
                    ns = None
                
                if in_page:
                    page_content += line
                    
                    # Extract title
                    if '<title>' in line and '</title>' in line:
                        match = re.search(r'<title>(.*?)</title>', line)
                        if match:
                            title = match.group(1)
                    
                    # Extract namespace
                    if '<ns>' in line and '</ns>' in line:
                        match = re.search(r'<ns>(\d+)</ns>', line)
                        if match:
                            ns = int(match.group(1))
                
                if '</page>' in line:
                    in_page = False
                    stats["pages_found"] += 1
                    
                    # Check namespace
                    if ns == 0 and title:
                        stats["main_namespace"] += 1
                        
                        # ACTUALLY extract text
                        text_match = re.search(r'<text[^>]*>(.*?)</text>', 
                                             page_content, re.DOTALL)
                        
                        if text_match:
                            wikitext = text_match.group(1)
                            
                            # Count actual links
                            links = re.findall(r'\[\[([^\[\]\|#]+)(?:\|[^\[\]]*)?\]\]', 
                                             wikitext[:50000])  # Limit search
                            
                            # Store sample
                            if len(sample_articles) < 5:
                                sample_articles.append({
                                    "title": title,
                                    "text_length": len(wikitext),
                                    "link_count": len(links),
                                    "sample_links": links[:3] if links else []
                                })
                        
                        # Progress update
                        if stats["main_namespace"] % 10 == 0:
                            elapsed = time.time() - stats["start_time"]
                            speed = stats["main_namespace"] / elapsed if elapsed > 0 else 0
                            print(f"  Processed {stats['main_namespace']} articles "
                                  f"({speed:.1f} articles/sec)")
                    
                    # Check limit
                    if stats["main_namespace"] >= 100:
                        break
        
        # Calculate final stats
        elapsed = time.time() - stats["start_time"]
        
        print("\n" + "=" * 60)
        print("📊 REAL PERFORMANCE RESULTS")
        print("=" * 60)
        
        print(f"\n⏱️  TIMING:")
        print(f"   Total time: {elapsed:.2f} seconds")
        print(f"   Articles processed: {stats['main_namespace']}")
        print(f"   Processing speed: {stats['main_namespace']/elapsed:.2f} articles/sec")
        
        print(f"\n📈 DATA:")
        print(f"   Total pages scanned: {stats['pages_found']}")
        print(f"   Main namespace pages: {stats['main_namespace']}")
        print(f"   Total characters read: {stats['total_chars_read']:,}")
        print(f"   Read speed: {stats['total_chars_read']/elapsed/1024/1024:.2f} MB/sec")
        
        print(f"\n💾 MEMORY:")
        print(f"   Peak memory: {stats['peak_memory_mb']:.1f} MB")
        current_mem = f"   Current memory: {psutil.Process().memory_info().rss / 1024 / 1024:.1f} MB" if psutil_available else "   Current memory: unknown"
        print(current_mem)
        
        print(f"\n🔍 SAMPLE ARTICLES:")
        for i, article in enumerate(sample_articles[:3]):
            print(f"\n   {i+1}. {article['title']}")
            print(f"      Text length: {article['text_length']:,} chars")
            print(f"      Links found: {article['link_count']}")
            if article['sample_links']:
                print(f"      Sample links: {', '.join(article['sample_links'][:2])}")
        
        # Check Polish characters
        print(f"\n🔤 POLISH CHARACTERS:")
        polish_found = False
        for article in sample_articles:
            if any(c in article['title'] for c in 'ąćęłńóśźż'):
                print(f"   ✓ Found in: {article['title']}")
                polish_found = True
                break
        if not polish_found:
            print("   ⚠️ No Polish diacritics found in sample")
        
        print("\n" + "=" * 60)
        
        # Save results
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "stats": stats,
            "sample_articles": sample_articles,
            "elapsed_seconds": elapsed,
            "articles_per_second": stats["main_namespace"] / elapsed
        }
        
        with open(output_dir / "real_performance.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved to: output/real_performance.json")
        
        # Decision logic
        print(f"\n🎯 DECISION POINT:")
        speed = stats["main_namespace"] / elapsed
        
        if speed > 100:
            print(f"   ⚠️  Speed {speed:.1f} articles/sec - TOO FAST (likely not processing content)")
            print(f"   Action: Need to fix parsing logic")
            return False
        elif speed > 50:
            print(f"   ✅ Speed {speed:.1f} articles/sec - EXCELLENT")
            print(f"   Action: Ready to scale up")
            return True
        elif speed > 20:
            print(f"   ⚠️  Speed {speed:.1f} articles/sec - ACCEPTABLE")
            print(f"   Action: Consider copying to WSL for better speed")
            return True
        else:
            print(f"   ❌ Speed {speed:.1f} articles/sec - TOO SLOW")
            print(f"   Action: Must copy to WSL filesystem")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
