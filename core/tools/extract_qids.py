import gzip
import re
import os
import requests
import argparse
from pathlib import Path

class QidResolverBuilder:
    def __init__(self, base_data_dir="data"):
        self.base_dir = Path(base_data_dir)
        self.raw_dir = self.base_dir / "raw"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir = self.base_dir / "processed"
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
    def download_props(self, lang):
        url = f"https://dumps.wikimedia.org/{lang}wiki/latest/{lang}wiki-latest-page_props.sql.gz"
        dest = self.raw_dir / f"{lang}wiki-latest-page_props.sql.gz"
        
        if dest.exists():
            print(f"✅ {lang} page_props already exists at {dest}.")
            return dest
            
        print(f"📥 Downloading {lang} page_props (~50-100MB)...")
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(dest, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"✅ Download complete: {dest}")
        except Exception as e:
            print(f"❌ Failed to download {lang}: {e}")
            if dest.exists():
                dest.unlink()
            return None
        return dest

    def extract_mappings(self, sql_gz_path):
        """
        Parses SQL INSERT statements to extract (page_id, wikibase_item)
        Example: (123,'wikibase_item','Q456')
        Output CSV is derived from the input filename.
        """
        # Infer language from filename: e.g., "plwiki-latest..." -> "pl"
        filename = sql_gz_path.name
        lang_match = re.match(r"([a-z-]+)wiki-latest", filename)
        if not lang_match:
            print(f"⚠️ Skipping {filename}: Could not infer language code.")
            return

        lang = lang_match.group(1)
        output_csv = self.processed_dir / f"qids_{lang}.csv"
        
        print(f"🛠️ Extracting QIDs from {filename} -> {output_csv}...")
        
        # Regex to find (page_id, 'wikibase_item', 'QID')
        pattern = re.compile(r"\((\d+),'wikibase_item','(Q\d+)'")
        
        count = 0
        try:
            with gzip.open(sql_gz_path, 'rt', encoding='utf-8', errors='ignore') as f_in, \
                 open(output_csv, 'w', encoding='utf-8') as f_out:
                
                f_out.write("page_id,qid\n")
                
                for line in f_in:
                    if "INSERT INTO" in line:
                        matches = pattern.findall(line)
                        for page_id, qid in matches:
                            f_out.write(f"{page_id},{qid}\n")
                            count += 1
            print(f"✨ Extracted {count:,} QID mappings for '{lang}'.")
        except Exception as e:
            print(f"❌ Failed to extract {filename}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Extract QID mappings from Wikipedia page_props SQL dumps.")
    parser.add_argument("--lang", type=str, help="Language code to download and process (e.g., 'es', 'fr'). If omitted, processes all existing files.")
    args = parser.parse_args()

    builder = QidResolverBuilder()
    
    if args.lang:
        # User requested a specific language
        print(f"🚀 Processing requested language: {args.lang}")
        file_path = builder.download_props(args.lang)
        if file_path:
            builder.extract_mappings(file_path)
    else:
        # Scan mode: Process all matching files in data/raw
        print("🔍 Scanning data/raw for existing page_props dumps...")
        found = False
        for file_path in builder.raw_dir.glob("*wiki-latest-page_props.sql.gz"):
            found = True
            builder.extract_mappings(file_path)
        
        if not found:
            print("ℹ️ No files found. Use --lang <code_iso> to download one.")

if __name__ == "__main__":
    main()
