import os
import asyncio
import httpx
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

async def test_connections():
    print("--- DevPulseAI v2 Connection Tester ---\n")
    
    # 1. Test Supabase
    print("[1/3] Testing Supabase Connection...")
    supa_url = os.getenv("SUPABASE_URL")
    supa_key = os.getenv("SUPABASE_KEY")
    
    if not supa_url or not supa_key:
        print("❌ Supabase credentials missing.")
    else:
        try:
            # Simple query to check connection (raw_signals table existence)
            client = create_client(supa_url, supa_key)
            # Fetch 0 rows just to check auth/connectivity
            client.table("raw_signals").select("id").limit(1).execute()
            print("✅ Supabase Connected Successfully.")
        except Exception as e:
            print(f"❌ Supabase Connection Failed: {e}")

    # 2. Test GitHub
    print("\n[2/3] Testing GitHub Connection...")
    gh_token = os.getenv("GITHUB_TOKEN")
    if not gh_token:
        print("⚠️ GitHub Token missing (skipping).")
    else:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get("https://api.github.com/user", headers={"Authorization": f"Bearer {gh_token}", "User-Agent": "DevPulseAI"})
                if resp.status_code == 200:
                    print(f"✅ GitHub Connected as {resp.json().get('login')}.")
                else:
                    print(f"❌ GitHub Failed: {resp.status_code} {resp.text}")
        except Exception as e:
            print(f"❌ GitHub Check Failed: {e}")

    # 3. Test Bytez.com
    print("\n[3/3] Testing Bytez.com Connection...")
    bytez_key = os.getenv("BYTEZ_API_KEY")
    if not bytez_key:
        print("❌ Bytez API Key missing.")
    else:
        # Assuming we can hit a 'list models' or similar lightweight endpoint
        # If not, we try a very cheap/simple completion or check if there's a health check
        # Based on typical API patterns:
        url = "https://api.bytez.com/v1/models" 
        headers = {"Authorization": f"Bearer {bytez_key}"}
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    print("✅ Bytez.com Connection Verified (Models list accessible).")
                elif resp.status_code == 401:
                     print("❌ Bytez.com Unauthorized (Check API Key).")
                else:
                    print(f"⚠️ Bytez.com returned {resp.status_code} (This might be normal if /models endpoint differs): {resp.text}")
        except Exception as e:
            print(f"❌ Bytez.com Connection Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connections())
