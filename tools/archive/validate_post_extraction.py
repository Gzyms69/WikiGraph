#!/usr/bin/env python3
"""
tools/validate_post_extraction.py
Post-extraction validation for German Wikipedia after re-extraction.
Run this AFTER extraction completes.
"""

import sqlite3
import json
import random
from collections import Counter

def validate_german_completion():
    """Validate German extraction results"""
    print("🔍 Validating German extraction completion...")
    
    conn = sqlite3.connect('data/db/de.db')
    
    # 1. Yield calculation
    cursor = conn.execute("""
        SELECT 
            COUNT(*) as total_canonical,
            COUNT(infobox) as with_infobox,
            ROUND(COUNT(infobox)*100.0/COUNT(*), 2) as percentage
        FROM pages WHERE namespace=0 AND is_redirect=0
    """)
    total, with_ib, percentage = cursor.fetchone()
    print(f"\n📊 GERMAN YIELD:")
    print(f"   Total canonical articles: {total:,}")
    print(f"   With infoboxes: {with_ib:,}")
    print(f"   Percentage: {percentage}%")
    
    # 2. Template distribution
    print(f"\n📋 TEMPLATE DISTRIBUTION:")
    cursor = conn.execute("SELECT infobox FROM pages WHERE infobox IS NOT NULL")
    stats = Counter()
    
    for (ib_json,) in cursor:
        try:
            data = json.loads(ib_json)
            if not data:
                continue
            for tmpl in data:
                name = tmpl.get('template', '').strip()
                if name == 'Taxobox':
                    stats['Taxobox'] += 1
                elif name == 'Personendaten':
                    stats['Personendaten'] += 1
                elif name.startswith('Infobox'):
                    stats['Infobox'] += 1
                else:
                    stats['Other'] += 1
        except json.JSONDecodeError:
            stats['Invalid JSON'] += 1
    
    for template, count in stats.most_common():
        print(f"   {template}: {count:,}")
    
    # 3. JSON integrity check (1000 random samples)
    print(f"\n✅ JSON INTEGRITY CHECK (1,000 random samples):")
    cursor = conn.execute("""
        SELECT infobox FROM pages 
        WHERE infobox IS NOT NULL 
        ORDER BY RANDOM() LIMIT 1000
    """)
    errors = 0
    for (ib_json,) in cursor:
        try:
            if ib_json and ib_json.strip() and ib_json not in ['null', 'NULL']:
                json.loads(ib_json)
        except:
            errors += 1
    
    error_rate = (errors / 1000) * 100
    print(f"   Errors: {errors}/1000 ({error_rate:.2f}%)")
    
    conn.close()
    
    return total, with_ib, percentage, stats, errors

def compare_pl_de_overlap():
    """Compare 20 random articles that exist in both PL and DE"""
    print("\n🌐 COMPARING PL vs DE (20 overlapping articles):")
    
    # Connect to both databases
    de_conn = sqlite3.connect('data/db/de.db')
    pl_conn = sqlite3.connect('data/db/pl.db')
    
    # Find overlapping QIDs (articles that exist in both)
    de_cursor = de_conn.execute("""
        SELECT DISTINCT m.qid 
        FROM id_mapping m
        JOIN pages p ON m.page_id = p.page_id
        WHERE p.infobox IS NOT NULL
        LIMIT 500
    """)
    de_qids = {row[0] for row in de_cursor.fetchall()}
    
    pl_cursor = pl_conn.execute("""
        SELECT DISTINCT m.qid 
        FROM id_mapping m
        JOIN pages p ON m.page_id = p.page_id
        WHERE p.infobox IS NOT NULL
        LIMIT 500
    """)
    pl_qids = {row[0] for row in pl_cursor.fetchall()}
    
    overlapping = list(de_qids.intersection(pl_qids))
    
    if not overlapping:
        print("   No overlapping articles found.")
        return

    if len(overlapping) < 20:
        print(f"   Only found {len(overlapping)} overlapping articles with infoboxes")
        sample_qids = overlapping
    else:
        sample_qids = random.sample(overlapping, 20)
    
    print(f"   Found {len(overlapping)} overlapping articles with infoboxes")
    print(f"   Sampling {len(sample_qids)} for comparison\n")
    
    for i, qid in enumerate(sample_qids, 1):
        # Get DE infobox
        de_cursor = de_conn.execute("""
            SELECT p.infobox, p.title
            FROM pages p
            JOIN id_mapping m ON p.page_id = m.page_id
            WHERE m.qid = ? AND p.infobox IS NOT NULL
            LIMIT 1
        """, (qid,))
        de_result = de_cursor.fetchone()
        
        # Get PL infobox
        pl_cursor = pl_conn.execute("""
            SELECT p.infobox, p.title
            FROM pages p
            JOIN id_mapping m ON p.page_id = m.page_id
            WHERE m.qid = ? AND p.infobox IS NOT NULL
            LIMIT 1
        """, (qid,))
        pl_result = pl_cursor.fetchone()
        
        if de_result and pl_result:
            de_ib, de_title = de_result
            pl_ib, pl_title = pl_result
            
            # Extract template names
            de_templates = []
            pl_templates = []
            
            try:
                de_data = json.loads(de_ib)
                de_templates = [t.get('template', '') for t in de_data if t.get('template')]
            except:
                de_templates = ['Parse Error']
            
            try:
                pl_data = json.loads(pl_ib)
                pl_templates = [t.get('template', '') for t in pl_data if t.get('template')]
            except:
                pl_templates = ['Parse Error']
            
            print(f"{i:2d}. {qid}")
            print(f"    DE: {de_title[:40]}... → Templates: {', '.join(de_templates)}")
            print(f"    PL: {pl_title[:40]}... → Templates: {', '.join(pl_templates)}")
            print()
    
    de_conn.close()
    pl_conn.close()

def main():
    """Main validation routine"""
    print("=" * 60)
    print("POST-EXTRACTION VALIDATION SCRIPT")
    print("=" * 60)
    
    # Validate German completion
    total, with_ib, percentage, stats, errors = validate_german_completion()
    
    # Compare PL vs DE
    compare_pl_de_overlap()
    
    # Success criteria check
    print("\n🎯 SUCCESS CRITERIA CHECK:")
    success = True
    
    if percentage >= 45:
        print(f"   ✅ Yield: {percentage}% (target: ≥45%)")
    else:
        print(f"   ❌ Yield: {percentage}% (target: ≥45%)")
        success = False
    
    if errors <= 10:  # Less than 1% errors
        print(f"   ✅ JSON errors: {errors}/1000 (target: ≤10)")
    else:
        print(f"   ❌ JSON errors: {errors}/1000 (target: ≤10)")
        success = False
    
    if stats['Taxobox'] > 50000:
        print(f"   ✅ Taxobox count: {stats['Taxobox']:,} (target: >50k)")
    else:
        print(f"   ❌ Taxobox count: {stats['Taxobox']:,} (target: >50k)")
        success = False
    
    if stats['Personendaten'] > 300000:
        print(f"   ✅ Personendaten count: {stats['Personendaten']:,} (target: >300k)")
    else:
        print(f"   ❌ Personendaten count: {stats['Personendaten']:,} (target: >300k)")
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✅ VALIDATION PASSED - Ready for Phase 2 (API Restoration)")
    else:
        print("⚠️  VALIDATION WARNING - Some targets not met")
    print("=" * 60)

if __name__ == "__main__":
    main()
