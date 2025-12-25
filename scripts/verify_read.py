
import asyncio
import os
from app.persistence.client import db

async def verify_read():
    print("--- Verifying DB Read Access ---")
    try:
        # Try simple select without count
        print("Attempting simple select...")
        res = db.get_client().table("raw_signals").select("id").limit(1).execute()
        print(f"Result data len: {len(res.data) if res.data else 0}")
        print("SUCCESS: Read works.")
    except Exception as e:
        print(f"FAILURE: {e}")
        # Print details if possible
        if hasattr(e, 'message'): print(e.message)

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify_read())
