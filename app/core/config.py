import yaml
import os
from pathlib import Path

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
            # Ensure paths are absolute or correct relative to CWD if needed
            # But the logic uses 'ports' mainly.
            print("⚠️  RUNNING IN TEST MODE (Using Test Ports) ⚠️")
            
    return config

settings = load_config()