import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from config.language_manager import LanguageManager

def test_language_accessors(lang_code):
    print(f"\n=== Testing Language: {lang_code} ===")
    
    try:
        # 1. Load Config
        print(f"Loading config...")
        try:
            config = LanguageManager.get_config(lang_code)
            print("Config loaded.")
        except Exception as e:
            print(f"Config Load Failed: {type(e).__name__}: {e}")
            return # Stop if config load fails (unless we want to test JIT failure)

        # 2. Test Each Accessor
        accessors = [
            ('get_text_cleanup_patterns', 'Text Cleanup'),
            ('get_redirect_keywords', 'Redirect Keywords'),
            ('get_namespace_prefixes', 'Namespace Prefixes'),
            ('get_dbname', 'DB Name'),
            ('get_language_info', 'Language Info'),
            ('get_processing_config', 'Processing Config')
        ] 
        
        for method_name, label in accessors:
            print(f"Testing {label} ({method_name})...", end=" ")
            try:
                method = getattr(LanguageManager, method_name)
                result = method(lang_code)
                print(f"OK. Type: {type(result).__name__}, Value: {result}")
            except Exception as e:
                print(f"CRASH: {type(e).__name__}: {e}")

    except Exception as e:
         print(f"Fatal Error in Test Harness: {e}")

if __name__ == "__main__":
    print("=== WikiGraph LanguageManager Accessor Validation ===")
    
    # 1. Full Configs (Should PASS all)
    test_language_accessors('de')
    test_language_accessors('pl')
    
    # 2. Partial Config (Should PASS modified, FAIL others)
    test_language_accessors('en')
    
    # 3. Missing Config (Should FAIL load)
    test_language_accessors('es')
