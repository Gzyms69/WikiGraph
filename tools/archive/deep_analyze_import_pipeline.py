import os
import sys

def analyze_csv_generation():
    """Analyze ACTUAL CSV generation, not just patterns"""
    
    print("=== DEEP ANALYSIS OF IMPORT PIPELINE ===")
    
    # 1. Check if CSV files exist
    csv_search_paths = [
        "data/neo4j_data/pl/import/nodes.csv",
        "data/neo4j_data/de/import/nodes.csv",
        "data/neo4j_bulk/pl/nodes.csv",
        "data/neo4j_bulk/de/nodes.csv",
        "data/neo4j_bulk/pl/nodes_header.csv",
        "data/neo4j_bulk/de/nodes_header.csv"
    ]
    
    print("\n--- CSV FILE INSPECTION ---")
    for path in csv_search_paths:
        if os.path.exists(path):
            print(f"\n📁 FOUND: {path}")
            # Show header and first row
            try:
                with open(path, 'r') as f:
                    # Read first few bytes to check for header
                    header = f.readline().strip()
                    first_row = f.readline().strip()
                    print(f"   Line 1: {header}")
                    print(f"   Line 2: {first_row}")
            except Exception as e:
                print(f"   Error reading: {e}")
        else:
            print(f"❌ MISSING: {path}")
    
    # 2. Analyze prepare_neo4j_csv.py ACTUAL code
    print("\n\n--- PREPARE_NEO4J_CSV.PY ACTUAL CODE ---")
    script_path = "core/tools/prepare_neo4j_csv.py"
    if os.path.exists(script_path):
        with open(script_path, 'r') as f:
            content = f.read()
            
        lines = content.split('\n')
        for i, line in enumerate(lines):
            # Look for header definitions
            if "header" in line or "writerow" in line or "nodes_header" in line:
                print(f"Line {i+1}: {line.strip()}")
    else:
        print(f"❌ Script not found: {script_path}")
    
    # 3. Analyze run_neo4j_import.sh ACTUAL command
    print("\n\n--- RUN_NEO4J_IMPORT.SH ACTUAL COMMAND ---")
    sh_path = "core/tools/run_neo4j_import.sh"
    if os.path.exists(sh_path):
        with open(sh_path, 'r') as f:
            import_script = f.read()
        
        # Find neo4j-admin command
        for line in import_script.split('\n'):
            if "neo4j-admin" in line and "import" in line:
                print(f"Import command: {line.strip()}")
    else:
        print(f"❌ Script not found: {sh_path}")
    
if __name__ == "__main__":
    analyze_csv_generation()
