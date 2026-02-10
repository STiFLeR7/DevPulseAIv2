import os
import uuid
from dotenv import load_dotenv
from supabase import create_client

# Force reload of .env
load_dotenv(override=True)

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

print("Testing Supabase Connection with Detailed Error Info")
print("="*60)

try:
    client = create_client(url, key)
    print("✓ Client created")
    
    # Try a simple insert
    test_data = {
        "run_id": str(uuid.uuid4()),
        "agent_name": "TestAgent",
        "step_name": "test_step",
        "input_state": {"test": "input"},
        "output_state": {"test": "output"},
        "status": "completed"
    }
    
    print(f"\nAttempting to insert test record...")
    result = client.table("agent_traces").insert(test_data).execute()
    print(f"✅ SUCCESS! Inserted record: {result.data}")
    
    # Try to read it back
    print(f"\nAttempting to read records...")
    read_result = client.table("agent_traces").select("*").limit(1).execute()
    print(f"✅ SUCCESS! Found {len(read_result.data)} records")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    print(f"\nError type: {type(e).__name__}")
    if hasattr(e, 'args'):
        print(f"Error args: {e.args}")
