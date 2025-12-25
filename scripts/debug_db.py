import os
import sys
from dotenv import load_dotenv
from supabase import create_client

sys.path.append(os.getcwd())
load_dotenv(override=True)

def debug_supabase():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    client = create_client(url, key)
    
    print(f"Checking {url}...")
    
    # 1. Simply try to select from the table.
    # Note: If RLS is ON and Service Role Key is NOT used, this might fail or return empty.
    # But PGRST205 usually means table doesn't exist in the Exposed Schema (public).
    
    try:
        print("Stubbing insert to check schema...")
        # Using a select with limit 1 is safer than insert
        res = client.table("raw_signals").select("id").limit(1).execute()
        print(f"✅ Table Found. Rows: {len(res.data)}")
    except Exception as e:
        print(f"❌ Read Failed: {e}")
        
    # Check 'processed_intelligence'
    try:
        res = client.table("processed_intelligence").select("id").limit(1).execute()
        print(f"✅ Intelligence Table Found.")
    except Exception as e:
        print(f"❌ Intelligence Read Failed: {e}")

if __name__ == "__main__":
    debug_supabase()
