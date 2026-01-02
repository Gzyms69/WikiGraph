import csv
import sys
from pathlib import Path

def clean_data_tsv_safe():
    import_dir = Path('data/neo4j_import')
    clean_dir = Path('data/neo4j_import_clean')
    clean_dir.mkdir(exist_ok=True)

    node_ids = set()
    
    # 1. Process Nodes
    for label in ['articles', 'aliases']:
        out_path = clean_dir / f'{label}_clean.tsv'
        print(f"Cleaning {label} nodes and converting to TSV (Safe Mode)...")
        
        with open(out_path, 'w', encoding='utf-8', newline='') as fout:
            writer = None
            for lang in ['pl', 'de']:
                in_path = import_dir / f'{label}_{lang}.csv'
                if not in_path.exists(): continue
                
                with open(in_path, 'r', encoding='utf-8') as fin:
                    reader = csv.DictReader(fin)
                    if not writer:
                        fieldnames = reader.fieldnames
                        # QUOTE_MINIMAL is the professional standard. 
                        # It only quotes if it finds a delimiter (\t) inside the text.
                        writer = csv.DictWriter(fout, fieldnames=fieldnames, delimiter='\t', quoting=csv.QUOTE_MINIMAL)
                        writer.writeheader()
                    
                    for row in reader:
                        nid = row['id:ID']
                        if nid not in node_ids:
                            node_ids.add(nid)
                            # Remove tabs from titles to ensure zero quoting happens
                            row['title:STRING'] = row['title:STRING'].replace('\t', ' ')
                            writer.writerow(row)
    
    print(f"Total unique nodes: {len(node_ids):,}")

    # 2. Process Relationships (Streaming)
    for rel_type in ['links', 'redirects']:
        out_path = clean_dir / f'{rel_type}_clean.tsv'
        print(f"Cleaning {rel_type} relationships and converting to TSV (Safe Mode)...")
        
        with open(out_path, 'w', encoding='utf-8', newline='') as fout:
            writer = None
            for lang in ['pl', 'de']:
                in_path = import_dir / f'{rel_type}_{lang}.csv'
                if not in_path.exists(): continue
                
                with open(in_path, 'r', encoding='utf-8') as fin:
                    reader = csv.DictReader(fin)
                    if not writer:
                        writer = csv.DictWriter(fout, fieldnames=reader.fieldnames, delimiter='\t', quoting=csv.QUOTE_MINIMAL)
                        writer.writeheader()
                    
                    for row in reader:
                        # Only keep if both nodes exist in our clean set
                        if row[':START_ID'] in node_ids and row[':END_ID'] in node_ids:
                            writer.writerow(row)

    print("✅ Data cleaning and TSV conversion complete.")

if __name__ == "__main__":
    clean_data_tsv_safe()
