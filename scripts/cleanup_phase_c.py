#!/usr/bin/env python3
"""
WikiGraph Phase C: "Project De-Clutter"
Moves legacy/debug scripts to archive folders.
"""

import os
import sys
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# --- Cleanup Targets ---
# Source Dir -> (Archive Dir, Exclude List)
TARGETS = {
    "core/tools": ("core/legacy", ["__pycache__"]),
    "tools": ("tools/archive", ["analytics", "ops", "archive", "__pycache__"]),
    "tests": ("tests/archive", ["unit", "integration", "archive", "__pycache__"]),
}

def cleanup():
    print("🧹 Starting Phase C Cleanup...")
    total_moved = 0

    for src_name, (archive_name, exclude_list) in TARGETS.items():
        src_dir = PROJECT_ROOT / src_name
        archive_dir = PROJECT_ROOT / archive_name
        
        # Ensure archive dir exists
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        if not src_dir.exists():
            print(f"⚠️  Source not found: {src_name}")
            continue

        print(f"\n📂 Processing {src_name} -> {archive_name}...")
        
        # List files to move
        files_to_move = []
        for item in src_dir.iterdir():
            if item.name in exclude_list:
                continue
            if item.is_dir() and item.name == archive_name.split("/")[-1]:
                 # Don't move the archive folder into itself (e.g. tools/archive)
                 continue
            files_to_move.append(item)
        
        # Execute Moves
        for item in files_to_move:
            dest = archive_dir / item.name
            try:
                shutil.move(str(item), str(dest))
                print(f"  ✅ Archived: {item.name}")
                total_moved += 1
            except Exception as e:
                print(f"  ❌ Failed: {item.name} - {e}")

        # Special Case: Remove core/tools if empty
        if src_name == "core/tools":
            remaining = list(src_dir.iterdir())
            # Check if only __pycache__ remains
            if all(f.name == "__pycache__" for f in remaining):
                 shutil.rmtree(src_dir)
                 print(f"  🗑️  Removed empty directory: {src_name}")

    print(f"\n✨ Cleanup Complete. {total_moved} files archived.")

if __name__ == "__main__":
    cleanup()
