"""
Analyze the current import pipeline to understand data flow
"""
import os
import re

def analyze_import_scripts():
    print("="*60)
    print("IMPORT PIPELINE ANALYSIS")
    print("="*60)
    
    # Key directories and files
    import_scripts = [
        "core/ingest.py",
        "core/sqlite_loader.py", 
        "core/tools/run_neo4j_import.sh",
        "core/tools/prepare_neo4j_csv.py",
        "core/tools/fetch_sql_dumps.py"
    ]
    
    for script_path in import_scripts:
        if os.path.exists(script_path):
            print(f"\n📄 {script_path}:")
            
            with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # Extract key operations
                if 'prepare_neo4j_csv.py' in script_path:
                    print("  └─ Generates CSV files for Neo4j import")
                    if 'qid' in content:
                        print("     ├─ Includes: qid")
                    
                    # Check for title inclusion
                    has_title_header = "title" in content and ("header" in content or "csv.writer" in content)
                    if has_title_header:
                        print("     ├─ Includes: title (Logic found)")
                    else:
                        print("     ⚠️  DOES NOT INCLUDE: title (needs update)")
                
                elif 'sqlite_loader.py' in script_path:
                    print("  └─ Loads data into SQLite")
                    tables = re.findall(r'CREATE TABLE IF NOT EXISTS (\w+)', content, re.IGNORECASE)
                    if not tables:
                        tables = re.findall(r'CREATE TABLE (\w+)', content, re.IGNORECASE)
                    if tables:
                        print(f"     ├─ Creates tables: {', '.join(tables)}")
                
                elif 'run_neo4j_import.sh' in script_path:
                    print("  └─ Imports CSV into Neo4j")
                    if 'neo4j-admin database import' in content:
                         print("     ├─ Uses neo4j-admin import (bulk)")
                    elif 'LOAD CSV' in content:
                        print("     ├─ Uses LOAD CSV commands (cypher)")
                
                # Check for pagelinks processing
                if 'pagelink' in content.lower():
                    print("     ├─ Processes pagelinks data")
                
    
    print(f"\n{'='*60}")
    print("PIPELINE GAP ANALYSIS:")
    print(f" { '='*60}")
    
    print("\n1. CURRENT PIPELINE STEPS (Inferred):")
    print("   1. Fetch SQL Dumps (fetch_sql_dumps.py)")
    print("   2. Load Metadata to SQLite (sqlite_loader.py)")
    print("   3. Prepare CSVs from Dumps (prepare_neo4j_csv.py)")
    print("   4. Bulk Import to Neo4j (run_neo4j_import.sh)")
    
    print("\n2. IDENTIFIED GAPS:")
    print("   - Title Inclusion: Check prepare_neo4j_csv.py details.")
    print("   - Degree Computation: Not found in standard scripts.")

if __name__ == "__main__":
    analyze_import_scripts()
