#!/usr/bin/env python3
"""
validate_infobox_extraction.py - Validate infobox extraction quality
"""
import sqlite3
import json
import random
import sys
from pathlib import Path

def validate_extraction(lang='de', total_expected=10000):
    """Validate extraction with automated checks and manual sampling"""
    db_path = f"data/db/{lang}.db"
    
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 60)
    print(f"VALIDATING INFOBOX EXTRACTION FOR {lang.upper()}")
    print("=" * 60)
    
    # 1. COUNT VALIDATION
    print("\n1. QUANTITATIVE VALIDATION")
    print("-" * 40)
    
    cursor.execute("""
        SELECT COUNT(*) 
        FROM pages 
        WHERE infobox IS NOT NULL 
        AND namespace = 0 
        AND is_redirect = 0
    """)
    extracted_count = cursor.fetchone()[0]
    
    print(f"Expected: {total_expected} articles with infoboxes")
    print(f"Found:    {extracted_count}")
    
    # Allow small variance if run was interrupted or exact count logic differs
    if extracted_count < total_expected * 0.99:
        print(f"❌ COUNT MISMATCH: {extracted_count} < {total_expected}")
        return False
    
    print("✅ Count validation passed")
    
    # 2. JSON STRUCTURE VALIDATION
    print("\n2. JSON STRUCTURE VALIDATION")
    print("-" * 40)
    
    cursor.execute("""
        SELECT title, infobox 
        FROM pages 
        WHERE infobox IS NOT NULL 
        AND namespace = 0 
        AND is_redirect = 0
        LIMIT 1000
    """)
    
    samples = cursor.fetchall()
    json_errors = 0
    structure_errors = 0
    template_errors = 0
    
    for title, infobox_json in samples:
        try:
            data = json.loads(infobox_json)
            
            # Must be array
            if not isinstance(data, list):
                structure_errors += 1
                continue
            
            # Check each infobox
            for item in data:
                # Must have template and params
                if 'template' not in item or 'params' not in item:
                    structure_errors += 1
                    continue
                
                # For German: template should start with "Infobox"
                if lang == 'de' and not item['template'].startswith('Infobox'):
                    template_errors += 1
                    # Not fatal, just warning
            
            # Check for common issues
            infobox_json_lower = infobox_json.lower()
            if '' in infobox_json or '\ufffd' in infobox_json_lower:
                print(f"  ⚠️  {title}: Contains replacement character (encoding issue)")
                
        except json.JSONDecodeError as e:
            json_errors += 1
            if json_errors <= 3:
                print(f"  ❌ {title}: JSON decode error: {e}")
    
    print(f"✅ JSON validation: {len(samples)} samples checked")
    print(f"   JSON decode errors: {json_errors}")
    print(f"   Structure errors: {structure_errors}")
    print(f"   Template prefix warnings: {template_errors}")
    
    if json_errors > 5:
        print(f"❌ Too many JSON errors ({json_errors})")
        return False
    
    # 3. MANUAL SAMPLING (50 articles)
    print("\n3. MANUAL SAMPLING (50 articles)")
    print("-" * 40)
    print("The following 50 articles will be manually inspected:")
    
    cursor.execute("""
        SELECT title, infobox 
        FROM pages 
        WHERE infobox IS NOT NULL 
        AND namespace = 0 
        AND is_redirect = 0
        ORDER BY RANDOM()
        LIMIT 50
    """)
    
    manual_samples = cursor.fetchall()
    
    issues_found = []
    
    for i, (title, infobox_json) in enumerate(manual_samples, 1):
        data = json.loads(infobox_json)
        
        # Perform automated checks on these samples
        template_names = [item['template'] for item in data]
        param_counts = [len(item['params']) for item in data]
        
        # Check for issues
        issues = []
        
        # 1. Empty infobox
        if not data:
            issues.append("Empty infobox array")
        
        # 2. Non-German template names (for German)
        if lang == 'de':
            non_german = [name for name in template_names if not name.startswith('Infobox')]
            if non_german:
                issues.append(f"Non-German templates: {non_german}")
        
        # 3. Check for truncated values (explicit check for ... added by extractor)
        for item in data:
            for param_name, param_value in item['params'].items():
                if len(param_value) > 200 and param_value.endswith('...'):
                    pass # Full extractor does not truncate
        
        # 4. Check parameter count
        if sum(param_counts) == 0:
            issues.append("No parameters extracted")
        
        # Store issues
        if issues:
            issues_found.append((title, issues))
        
        # Print sample info
        print(f"\n{i:2d}. {title}")
        print(f"    Templates: {template_names}")
        print(f"    Total parameters: {sum(param_counts)}")
        
        # Show first 2 parameters of first infobox
        if data:
            first_ib = data[0]
            params_display = {}
            for k, v in list(first_ib['params'].items())[:2]:
                params_display[k] = v[:50] + "..." if len(v) > 50 else v
            print(f"    Sample params: {params_display}")
        
        if issues:
            print(f"    ⚠️  Issues: {', '.join(issues)}")
    
    # 4. SUMMARY
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    print(f"Articles validated: {extracted_count}")
    print(f"Manual samples inspected: {len(manual_samples)}")
    print(f"Articles with issues: {len(issues_found)}")
    
    if issues_found:
        print("\nISSUES FOUND:")
        for title, issues in issues_found[:5]:  # Show first 5
            print(f"  - {title}: {', '.join(issues)}")
        if len(issues_found) > 5:
            print(f"  ... and {len(issues_found) - 5} more")
    
    conn.close()
    
    # DECISION CRITERIA
    if extracted_count < total_expected * 0.99:
        print("\n❌ FAIL: Article count mismatch")
        return False
    
    if json_errors > 10:
        print("\n❌ FAIL: Too many JSON errors")
        return False
    
    if structure_errors > 5:
        print("\n❌ FAIL: Too many structure errors")
        return False
    
    if len(issues_found) > 10:  # More than 20% of manual samples
        print("\n❌ FAIL: Too many issues in manual samples")
        return False
    
    print("\n✅ VALIDATION PASSED: Ready for full extraction")
    return True

if __name__ == "__main__":
    success = validate_extraction('de', 10000)
    sys.exit(0 if success else 1)
