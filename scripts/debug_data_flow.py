import asyncio
import os
import sys
from dotenv import load_dotenv
from supabase import create_client

sys.path.append(os.getcwd())
load_dotenv(override=True)

from app.adapters.github import GitHubAdapter
from app.adapters.medium import MediumAdapter
from app.adapters.arxiv import ArXivAdapter

async def debug_data_flow():
    print("--- Debugging Data Flow ---")
    
    # 1. Test Adapters (Fetch Only)
    print("\n1. Testing Adapters (Fetch)...")
    try:
        gh = GitHubAdapter()
        items = await gh.fetch_trending()
        print(f"   GitHub Fetched: {len(items)} items")
        if len(items) > 0: print(f"   Sample: {items[0].payload['title']}")
    except Exception as e:
        print(f"   GitHub Failed: {e}")

    try:
        med = MediumAdapter()
        items = await med.fetch_feed_updates()
        print(f"   Medium Fetched: {len(items)} items")
    except Exception as e:
        print(f"   Medium Failed: {e}")
        
    try:
        arx = ArXivAdapter()
        items = await arx.fetch_recent_papers()
        print(f"   ArXiv Fetched: {len(items)} items")
    except Exception as e:
        print(f"   ArXiv Failed: {e}")

    # 2. Check Database counts
    print("\n2. Checking Database Counts...")
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    try:
        client = create_client(url, key)
        
        # Raw Signals
        res = client.table("raw_signals").select("*", count="exact").execute()
        print(f"   DB 'raw_signals' Count: {len(res.data)}")
        if len(res.data) > 0:
            print(f"   Last Signal Created At: {res.data[0]['created_at']}")
            print(f"   Last Signal Source: {res.data[0]['source']}")

        # Processed Intelligence
        res = client.table("processed_intelligence").select("*", count="exact").execute()
        print(f"   DB 'processed_intelligence' Count: {len(res.data)}")

    except Exception as e:
        print(f"   DB Check Failed: {e}")

if __name__ == "__main__":
    asyncio.run(debug_data_flow())
