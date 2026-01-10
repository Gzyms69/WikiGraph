#!/usr/bin/env python3
"""
CORE TOOL: Language Config Fetcher
----------------------------------
Dynamically generates project configuration YAMLs for any language
by querying the MediaWiki API.

This tool resolves the "Language Agnostic" scalability issue by
automating the discovery of:
1. Namespace prefixes (e.g., "Category:" vs "Kategoria:")
2. Redirect magic words (e.g., "#REDIRECT" vs "#PATRZ")
3. Database names (e.g., "plwiki")

Usage:
    python fetch_lang_config.py --lang pl
    python fetch_lang_config.py --lang fr --output config/languages/fr.yaml
"""

import argparse
import sys
import yaml
import requests
from pathlib import Path

def fetch_siteinfo(lang_code):
    """
    Query the MediaWiki API for site configuration.
    """
    url = f"https://{lang_code}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "meta": "siteinfo",
        "siprop": "general|namespaces|namespacealiases|magicwords",
        "format": "json"
    }
    
    print(f"📡 Querying {url}...")
    try:
        # Wikimedia API requires a User-Agent
        headers = {
            "User-Agent": "WikiGraph-ConfigFetcher/1.0 (local development; contact@example.com)"
        }
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if "query" not in data:
            raise ValueError(f"Invalid API response: {data}")
        return data["query"]
    except Exception as e:
        print(f"❌ API Request Failed: {e}")
        sys.exit(1)

def extract_redirect_keywords(magicwords):
    """
    Find 'redirect' magic word and its aliases.
    Example: ['#REDIRECT', '#WEITERLEITUNG']
    """
    for item in magicwords:
        if item["name"] == "redirect":
            # The API returns aliases without '#', usually? 
            # Actually siteinfo usually returns them WITH '#' or as is.
            # Let's verify. Based on docs, it returns e.g. "REDIRECT" and "WEITERLEITUNG".
            # But the parser expects the full string including '#'.
            # Wait, the search result said: "aliases": ["#REDIRECT", "#WEITERLEITUNG"]
            # So they include the hash. We will ensure they do.
            return item["aliases"]
    return ["#REDIRECT"] # Fallback

def extract_namespace_prefixes(namespaces, aliases):
    """
    Map canonical namespace IDs to all valid local prefixes.
    We care about:
    - 6: File
    - 10: Template
    - 14: Category
    """
    target_ids = {
        6: "file",
        10: "template",
        14: "category"
    }
    
    result = {k: [] for k in target_ids.values()}
    
    # 1. Get primary names from 'namespaces'
    for ns_id_str, info in namespaces.items():
        ns_id = int(ns_id_str)
        if ns_id in target_ids:
            key = target_ids[ns_id]
            # Add canonical name (e.g., "File")
            if info.get("canonical"):
                result[key].append(info["canonical"] + ":")
            # Add local name (e.g., "Plik")
            if info["*"] and info["*"] != info.get("canonical"):
                result[key].append(info["*"] + ":")
                
    # 2. Get aliases from 'namespacealiases'
    if aliases:
        for alias in aliases:
            ns_id = alias["id"]
            if ns_id in target_ids:
                key = target_ids[ns_id]
                # API returns alias like "Image" (no colon). We add colon.
                name = alias["*"] + ":"
                if name not in result[key]:
                    result[key].append(name)
                    
    return result

def generate_yaml(lang_code, output_path):
    siteinfo = fetch_siteinfo(lang_code)
    
    general = siteinfo["general"]
    namespaces = siteinfo["namespaces"]
    aliases = siteinfo.get("namespacealiases", [])
    magicwords = siteinfo.get("magicwords", [])
    
    # 1. Process Namespaces
    ns_prefixes = extract_namespace_prefixes(namespaces, aliases)
    
    # 2. Process Redirects
    redirects = extract_redirect_keywords(magicwords)
    
    # 3. Construct/Update Config Dict
    output_path = Path(output_path)
    
    if output_path.exists():
        print(f"🔄 Updating existing config at {output_path}")
        with open(output_path, 'r', encoding='utf-8') as f:
            existing_config = yaml.safe_load(f) or {}
    else:
        print(f"✨ Creating new config at {output_path}")
        existing_config = {}

    # Deep merge logic: Update only what we fetched, keep the rest
    if "language" not in existing_config:
        existing_config["language"] = {}
    existing_config["language"]["code"] = lang_code
    existing_config["language"]["name"] = general["sitename"]
    # Don't overwrite local_name if it exists (manual might be better)
    if "local_name" not in existing_config["language"]:
        existing_config["language"]["local_name"] = general.get("langname", lang_code)

    if "wikipedia" not in existing_config:
        existing_config["wikipedia"] = {}
    
    # Critical Updates
    existing_config["wikipedia"]["dbname"] = general["wikiid"]
    existing_config["wikipedia"]["redirect_keywords"] = redirects
    existing_config["wikipedia"]["namespace_prefixes"] = ns_prefixes
    
    # Ensure text_cleanup exists
    if "text_cleanup" not in existing_config:
        existing_config["text_cleanup"] = {}
    existing_config["text_cleanup"]["file_patterns"] = ns_prefixes["file"]

    # Text Processing Defaults (CJK Detection)
    if "text_processing" not in existing_config:
        existing_config["text_processing"] = {}
    
    # Known no-space languages
    no_space_langs = {"zh", "ja", "ko", "th", "vi", "km", "lo"}
    has_spaces = lang_code not in no_space_langs
    
    # Only set if not already manually configured
    if "has_spaces" not in existing_config["text_processing"]:
        existing_config["text_processing"]["has_spaces"] = has_spaces
        existing_config["text_processing"]["encoding"] = "utf-8"
    
    # 4. Write YAML
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(existing_config, f, allow_unicode=True, sort_keys=False)
    
    print(f"✅ Configuration successfully saved for '{lang_code}'")

def main():
    parser = argparse.ArgumentParser(description="Generate WikiGraph language config from MediaWiki API.")
    parser.add_argument("--lang", required=True, help="Language code (e.g., 'es', 'fr', 'ja')")
    parser.add_argument("--output", help="Custom output path. Defaults to config/languages/{lang}.yaml")
    
    args = parser.parse_args()
    
    # Determine output path
    if args.output:
        out_path = Path(args.output)
    else:
        # Resolve relative to project root (assuming script is in core/tools)
        project_root = Path(__file__).parent.parent.parent
        out_path = project_root / "config" / "languages" / f"{args.lang}.yaml"
        
    generate_yaml(args.lang, out_path)

if __name__ == "__main__":
    main()
