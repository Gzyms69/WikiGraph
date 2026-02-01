import os
import re

def find_import_scripts():
    print(f"\n{'='*60}")
    print(f"IMPORT SCRIPTS ANALYSIS")
    print(f"{ '='*60}")
    
    for root, dirs, files in os.walk('.'):
        if 'node_modules' in root or 'venv' in root or '.git' in root: continue
        for file in files:
            if file.endswith(('.py', '.sh', '.md')):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if 'pagelinks' in content.lower():
                            print(f"📄 {filepath}: Mentions 'pagelinks'")
                except: pass

if __name__ == "__main__":
    find_import_scripts()

