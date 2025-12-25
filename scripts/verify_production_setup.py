import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure root path
sys.path.append(os.getcwd())

from app.inference.client import BytezClient
from app.persistence.client import db

async def verify_production():
    print("--- DevPulseAI v2 Production Verification ---")
    load_dotenv()
    
    # 1. Supabase Check
    print("\n[1] Check Supabase...")
    try:
        # Assuming db init reads env
        client = db.get_client()
        res = client.table("raw_signals").select("count", count="exact").limit(0).execute()
        print(f"✅ Supabase Connected (Count: {res.count})")
    except Exception as e:
        print(f"❌ Supabase Failed: {e}")

    # 2. Bytez SDK Check
    print("\n[2] Check Bytez SDK (Model: meta-llama/Llama-3-8b-instruct)...")
    try:
        client = BytezClient()
        if not client.client:
            print("⚠️ Bytez SDK client is None (Check pip install bytez)")
        else:
            print("   Sending test prompt...")
            # We use a model we know is in the selector map, or from env
            model = "meta-llama/Llama-3-8b-instruct"
            response = await client.run_inference(model, "Say 'Hello DevPulse' if you can hear me.")
            
            content = response['choices'][0]['message']['content']
            print(f"✅ Bytez Response: {content[:100]}...")
    except Exception as e:
        print(f"❌ Bytez Failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify_production())
