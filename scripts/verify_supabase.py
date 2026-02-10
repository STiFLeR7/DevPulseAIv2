import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def verify_supabase():
    """Verify Supabase connection and credentials."""
    print("="*60)
    print("Supabase Environment Variables Check")
    print("="*60)
    
    # Check if variables are set
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    print(f"\n1. Environment Variables:")
    print(f"   SUPABASE_URL: {'✓ Set' if url else '✗ Missing'}")
    if url:
        print(f"   URL: {url}")
    print(f"   SUPABASE_KEY: {'✓ Set' if key else '✗ Missing'}")
    if key:
        print(f"   Key (first 10 chars): {key[:10]}...")
    
    if not url or not key:
        print("\n❌ Missing required environment variables!")
        return False
    
    # Test connection
    print(f"\n2. Testing Connection:")
    try:
        client = create_client(url, key)
        print("   ✓ Client created successfully")
        
        # Try to query a table (this will fail if auth is wrong)
        result = client.table("agent_traces").select("*").limit(1).execute()
        print("   ✓ Successfully queried 'agent_traces' table")
        print(f"   Records found: {len(result.data)}")
        
        print("\n✅ Supabase connection is working!")
        return True
        
    except Exception as e:
        print(f"   ✗ Connection failed: {e}")
        print("\n❌ Supabase authentication failed!")
        print("\nPossible issues:")
        print("  - Invalid API key (check SUPABASE_KEY)")
        print("  - Wrong project URL (check SUPABASE_URL)")
        print("  - Table 'agent_traces' does not exist (run schema.sql)")
        return False

if __name__ == "__main__":
    verify_supabase()
