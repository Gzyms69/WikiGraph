import yaml
import os
from pathlib import Path
import hashlib

def get_dynamic_ports(lang: str):
    """
    Stable Hash Fallback for port allocation.
    Matches logic in tools/ops/manage_containers.py
    """
    hash_val = int(hashlib.md5(lang.encode()).hexdigest(), 16)
    offset = hash_val % 100
    
    http_port = 7500 + offset
    bolt_port = 7713 + offset
    
    return {"http": http_port, "bolt": bolt_port}

def load_config(path: str = "config/infrastructure.yaml") -> dict:
    p = Path(path)
    if not p.exists():
        # Fallback for running from different CWD
        p = Path(__file__).resolve().parent.parent.parent / "config/infrastructure.yaml"
        
    if not p.exists():
        raise FileNotFoundError(f"Config not found: {path}")
        
    with open(p, "r") as f:
        config = yaml.safe_load(f)
        
    # Test Mode Override
    if os.getenv("TEST_MODE") == "true":
        if "test" in config and "languages" in config["test"]:
            config["languages"] = config["test"]["languages"]
            print("⚠️  RUNNING IN TEST MODE (Using Test Ports) ⚠️")

    # Dynamic Language Discovery Integration
    # We want to merge languages from config/languages/ into our settings
    # while respecting explicit overrides in infrastructure.yaml
    from config.language_manager import LanguageManager
    
    try:
        available_langs = LanguageManager.list_available_languages()
        if "languages" not in config:
            config["languages"] = {}
            
        for lang in available_langs:
            # If not already explicitly configured in infrastructure.yaml
            if lang not in config["languages"]:
                # Use JIT logic to determine ports
                ports = get_dynamic_ports(lang)
                
                # Check if the specific language config has port overrides
                try:
                    lang_config = LanguageManager.get_config(lang)
                    infra = lang_config.get('infrastructure', {})
                    if 'ports' in infra:
                        ports.update(infra['ports'])
                except Exception:
                    pass

                config["languages"][lang] = {
                    "enabled": True,
                    "ports": ports,
                    "container_name": f"wikigraph-neo4j-{lang}"
                }
    except Exception as e:
        # Don't let dynamic discovery crash the whole app if something is wrong
        import logging
        logging.getLogger(__name__).error(f"Dynamic language discovery failed: {e}")
            
    return config

settings = load_config()
