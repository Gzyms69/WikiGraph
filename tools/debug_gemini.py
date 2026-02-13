import os
import asyncio
from dotenv import load_dotenv
import google.generativeai as genai

async def main():
    print("--- Debugging Gemini Integration ---")
    
    # 1. Load .env
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    provider = os.getenv("AI_PROVIDER")
    
    print(f"AI_PROVIDER: {provider}")
    
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment.")
        return

    masked_key = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 10 else "***"
    print(f"API Key loaded: {masked_key}")

    # 2. Configure Gemini
    try:
        genai.configure(api_key=api_key)
        print("✅ genai.configure() called.")
    except Exception as e:
        print(f"❌ genai.configure() failed: {e}")
        return

    # 3. List Models (Verification)
    print("\n--- Listing Models ---")
    try:
        # Run sync for list_models
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
    except Exception as e:
        print(f"❌ Failed to list models: {e}")
        # Don't return, try generation anyway

    # 4. Generate Content
    print("\n--- Testing Generation ---")
    model_name = 'gemini-2.0-flash'
    try:
        model = genai.GenerativeModel(model_name)
        prompt = "Explain graph theory in one sentence."
        print(f"Sending prompt to {model_name}...")
        
        response = await model.generate_content_async(prompt)
        print(f"✅ Response received:\n{response.text}")
        
    except Exception as e:
        print(f"❌ Generation failed:")
        print(f"Type: {type(e)}")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
