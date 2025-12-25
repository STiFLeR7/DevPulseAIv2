import asyncio
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.getcwd())
load_dotenv(override=True)

from app.inference.gemini_client import GeminiClient

async def test_gemini():
    print("--- Testing Gemini 1.5 Flash ---")
    client = GeminiClient()
    if not client.model:
        print("❌ Client Init Failed (Check GEMINI_API_KEY)")
        return

    try:
        print("Sending prompt...")
        res = await client.run_inference("You are a ping bot.", "Reply only with 'PONG'.")
        print(f"✅ Response: {res['choices'][0]['message']['content']}")
    except Exception as e:
        print(f"❌ Inference Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_gemini())
