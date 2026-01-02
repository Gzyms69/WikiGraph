import gzip
import re
import os
import requests
from pathlib import Path

class QidResolverBuilder:
    def __init__(self, base_data_dir="data"):
        self.base_dir = Path(base_data_dir)
        self.raw_dir = self.base_dir / "raw"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        
    def download_props(self, lang):
        url = f"https://dumps.wikimedia.org/{lang}wiki/latest/{lang}wiki-latest-page_props.sql.gz"
        dest = self.raw_dir / f"{lang}wiki-latest-page_props.sql.gz"
        
        if dest.exists():
            print(f"✅ {lang} page_props already exists.")
            return dest
            
        print(f"📥 Downloading {lang} page_props (~50-100MB)...")
        response = requests.get(url, stream=True)
        with open(dest, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return dest

    def extract_mappings(self, sql_gz_path, output_csv):
        """
        Parses SQL INSERT statements to extract (page_id, wikibase_item)
        Example: (123,'wikibase_item','Q456')
        """
        print(f"🛠️ Extracting QIDs from {sql_gz_path.name}...")
        
        # Regex to find (page_id, 'wikibase_item', 'QID')
        # Format: (page_id,'wikibase_item','QID',...
        pattern = re.compile(r"\((\d+),'wikibase_item','(Q\d+)'")
        
        count = 0
        with gzip.open(sql_gz_path, 'rt', encoding='utf-8', errors='ignore') as f_in, \
             open(output_csv, 'w', encoding='utf-8') as f_out:
            
            f_out.write("page_id,qid\n")
            
            for line in f_in:
                if "INSERT INTO" in line:
                    matches = pattern.findall(line)
                    for page_id, qid in matches:
                        f_out.write(f"{page_id},{qid}\n")
                        count += 1
        
        print(f"✨ Extracted {count:,} QID mappings to {output_csv}")

def main():
    builder = QidResolverBuilder()
    
    # Process PL and DE for now
    for lang in ['pl', 'de']:
        sql_path = builder.download_props(lang)
        output_path = f"data/processed/qids_{lang}.csv"
        builder.extract_mappings(sql_path, output_path)

if __name__ == "__main__":
    main()
