import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

try:
    from app.services.ai_service import AIService, MockAIProvider, GeminiFlashProvider
    from app.api.v1.routers import ai
    print("✅ Imports successful")
    
    # Check default provider
    provider = AIService.get_provider()
    if isinstance(provider, MockAIProvider):
        print("✅ Default provider is MockAIProvider")
    else:
        print(f"❌ Default provider is {type(provider)}")

except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)
