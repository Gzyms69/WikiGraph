#!/usr/bin/env python3
"""
Library Test: mwsql (Phase 1, Gate 0) - Type Check
"""

import os
import sys
from pathlib import Path
from mwsql import Dump

def test_pl_categories():
    raw_dir = Path("data/raw")
    lt_dump_path = raw_dir / "plwiki-latest-linktarget.sql.gz"
    cl_dump_path = raw_dir / "plwiki-latest-categorylinks.sql.gz"

    print("🎯 Loading linktarget dump...")
    lt_dump = Dump.from_file(str(lt_dump_path), encoding='latin1')
    lt_map = {}
    
    # We need to find the specific IDs used in categorylinks: 1232641, 1621447, etc.
    # I'll just load all of them for Polish (it's small enough)
    for row in lt_dump.rows():
        try:
            lt_id = int(row[0])
            lt_title = row[2]
            lt_map[lt_id] = lt_title
        except (ValueError, IndexError):
            continue
    print(f"   Loaded {len(lt_map)} link targets.")

    print("🏷️ Loading categorylinks dump...")
    cl_dump = Dump.from_file(str(cl_dump_path), encoding='latin1')
    
    print("\n🔍 --- Success Criterion: Readable Categories ---")
    found_count = 0
    for row in cl_dump.rows():
        try:
            # row: (from, sortkey, timestamp, prefix, type, collation, target_id)
            p_from = row[0]
            target_id = int(row[6])
            resolved_name = lt_map.get(target_id)
            if resolved_name:
                print(f"   ✅ [Page ID {p_from}] -> Category: {resolved_name}")
                found_count += 1
        except (ValueError, IndexError):
            continue
            
        if found_count >= 10: break

    if found_count == 0:
        print("   ❌ Could not resolve any category names.")
        # Debug: check why mapping failed
        sample_ids = [1232641, 1621447, 1749534, 707271, 707275]
        print(f"   Checking sample IDs in map: {[id in lt_map for id in sample_ids]}")
    else:
        print(f"\n✅ Successfully resolved {found_count} category names.")

if __name__ == "__main__":
    test_pl_categories()
