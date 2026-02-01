import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from config.language_manager import LanguageManager

def test_language(lang_code):
    print(f"\n--- Testing Language: {lang_code} ---")
    try:
        # 1. Basic Load
        print(f"Loading config for '{lang_code}'...")
        config = LanguageManager.get_config(lang_code)
        print("Config loaded successfully.")
        
        # 2. Access Critical Section (The Crash Vector)
        print(f"Accessing 'text_cleanup' for '{lang_code}'...")
        patterns = LanguageManager.get_text_cleanup_patterns(lang_code)
        print(f"Success! Patterns found: {len(patterns)}")
        
    except KeyError as e:
        print(f"CRASH CONFIRMED: KeyError: {e}")
    except FileNotFoundError as e:
        print(f"CRASH CONFIRMED: FileNotFoundError: {e}")
    except Exception as e:
        print(f"CRASH CONFIRMED: {type(e).__name__}: {e}")

if __name__ == "__main__":
    print("=== WikiGraph Zero-Trust Crash Reproduction ===")
    
    # 1. Baseline (Should Work)
    test_language('de')
    test_language('pl')
    
    # 2. The Timebomb (Should Crash on KeyError)
    test_language('en')
    
    # 3. The Future State (Should Crash on FileNotFoundError)
    # We disable the JIT tool for this test to force the FileNotFoundError if config is missing
    # by mocking the existence check or just relying on the fact that es.yaml doesn't exist
    # and the fetch tool might fail or not be invoked if we don't mock it. 
    # However, LanguageManager logic tries to JIT. If JIT fails, it raises RuntimeError.
    # If JIT succeeds (it won't for 'es' without internet/mock), it raises RuntimeError.
    test_language('es')
