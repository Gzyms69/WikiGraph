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
import hashlib
from pathlib import Path

# --- Heuristics for Infobox Templates ---
# JIT cannot easily guess these, so we provide known defaults for major languages.
KNOWN_INFOBOX_PATTERNS = {
    "en": ["Infobox"],
    "es": ["Ficha", "Ficha de", "Infobox"],
    "fr": ["Infobox", "Modèle:Infobox"],
    "de": ["Infobox", "Taxobox", "Personendaten"], # Verified from Phase 5B
    "pl": ["Infobox", "Biogram infobox", "Organizacja infobox"], # Verified
    "pt": ["Info/", "Infobox"],
    "it": ["Infobox", "Box"],
    "ru": ["Infobox", "Карточка"],
    "ja": ["Infobox", "基礎情報"],
    "zh": ["Infobox", "信息框"],
}

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
        # In JIT context, we want to raise so the caller catches it
        raise

def extract_redirect_keywords(magicwords):
    """
    Find 'redirect' magic word and its aliases.
    Example: ['#REDIRECT', '#WEITERLEITUNG']
    """
    for item in magicwords:
        if item["name"] == "redirect":
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

def get_dynamic_ports(lang_code):
    """
    Calculate ports using the stable hash method (Shared with manage_containers.py).
    """
    hash_val = int(hashlib.md5(lang_code.encode()).hexdigest(), 16)
    offset = hash_val % 100
    
    http_port = 7500 + offset
    bolt_port = 7713 + offset
    return http_port, bolt_port

def generate_yaml(lang_code, output_path=None):
    try:
        siteinfo = fetch_siteinfo(lang_code)
    except Exception as e:
        print(f"Failed to fetch siteinfo: {e}")
        sys.exit(1)
    
    general = siteinfo["general"]
    namespaces = siteinfo["namespaces"]
    aliases = siteinfo.get("namespacealiases", [])
    magicwords = siteinfo.get("magicwords", [])
    
    # 1. Process Namespaces
    ns_prefixes = extract_namespace_prefixes(namespaces, aliases)
    
    # 2. Process Redirects
    redirects = extract_redirect_keywords(magicwords)
    
    # 3. Construct/Update Config Dict
    if output_path:
        out_path = Path(output_path)
    else:
        # Default path
        project_root = Path(__file__).resolve().parent.parent.parent
        out_path = project_root / "config" / "languages" / f"{lang_code}.yaml"

    if out_path.exists():
        print(f"🔄 Updating existing config at {out_path}")
        with open(out_path, 'r', encoding='utf-8') as f:
            existing_config = yaml.safe_load(f) or {}
    else:
        print(f"✨ Creating new config at {out_path}")
        existing_config = {}

    # --- Language Section ---
    if "language" not in existing_config:
        existing_config["language"] = {}
    existing_config["language"]["code"] = lang_code
    existing_config["language"]["name"] = general["sitename"]
    if "local_name" not in existing_config["language"]:
        existing_config["language"]["local_name"] = general.get("langname", lang_code)
    if "iso_code" not in existing_config["language"]:
        existing_config["language"]["iso_code"] = f"{lang_code}-{lang_code.upper()}"

    # --- Infrastructure Section (NEW) ---
    if "infrastructure" not in existing_config:
        http_port, bolt_port = get_dynamic_ports(lang_code)
        existing_config["infrastructure"] = {
            "ports": {
                "http": http_port,
                "bolt": bolt_port
            }
        }

    # --- Wikipedia Section ---
    if "wikipedia" not in existing_config:
        existing_config["wikipedia"] = {}
    
    existing_config["wikipedia"]["dbname"] = general["wikiid"]
    existing_config["wikipedia"]["base_url"] = general["base"]
    existing_config["wikipedia"]["api_url"] = f"https://{lang_code}.wikipedia.org/w/api.php"
    existing_config["wikipedia"]["redirect_keywords"] = redirects
    existing_config["wikipedia"]["namespace_prefixes"] = ns_prefixes
    
    # --- Text Cleanup Section ---
    if "text_cleanup" not in existing_config:
        existing_config["text_cleanup"] = {}
    # Default to file prefixes
    existing_config["text_cleanup"]["file_patterns"] = ns_prefixes["file"]

    # --- Processing Section ---
    if "processing" not in existing_config:
        existing_config["processing"] = {
            "enabled": True,
            "import_namespaces": [0, 14]
        }

    # --- Infobox Section ---
    if "infobox" not in existing_config:
        # Use known patterns if available, otherwise fallback to "Infobox"
        defaults = KNOWN_INFOBOX_PATTERNS.get(lang_code, ["Infobox"])
        existing_config["infobox"] = {
            "template_prefixes": defaults, 
            "template_suffixes": [],
            "parameter_map": {}
        }

    # --- UI Section ---
    if "ui" not in existing_config:
        existing_config["ui"] = {
            "search_placeholder": f"Search {general['sitename']}...",
            "language_name": general.get("langname", lang_code),
            "interface_translations": {
                "show_connections": "Show connections",
                "related_articles": "Related articles",
                "categories": "Categories"
            }
        }

    # --- Text Processing Defaults ---
    if "text_processing" not in existing_config:
        existing_config["text_processing"] = {}
    
    # Known no-space languages
    no_space_langs = {"zh", "ja", "ko", "th", "vi", "km", "lo"}
    has_spaces = lang_code not in no_space_langs
    
    if "has_spaces" not in existing_config["text_processing"]:
        existing_config["text_processing"]["has_spaces"] = has_spaces
        existing_config["text_processing"]["encoding"] = "utf-8"
    
    # 4. Write YAML
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(out_path, 'w', encoding='utf-8') as f:
        yaml.dump(existing_config, f, allow_unicode=True, sort_keys=False)
    
    # Output to stdout for capture by LanguageManager
    # (Though LanguageManager currently doesn't read stdout, it expects file creation)
    # But JIT implementation in LanguageManager subprocess might want to capture stdout if file write fails?
    # No, LanguageManager checks if file exists after run.
    print(f"✅ Configuration successfully saved for '{lang_code}'")

def main():
    parser = argparse.ArgumentParser(description="Generate WikiGraph language config from MediaWiki API.")
    parser.add_argument("--lang", required=True, help="Language code (e.g., 'es', 'fr', 'ja')")
    parser.add_argument("--output", help="Custom output path. Defaults to config/languages/{lang}.yaml")
    
    args = parser.parse_args()
    
    generate_yaml(args.lang, args.output)

if __name__ == "__main__":
    main()
