import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def check_tables():
    """Check which tables exist in the Supabase database."""
    print("="*60)
    print("Supabase Table Check")
    print("="*60)
    
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        print("❌ Missing SUPABASE_URL or SUPABASE_KEY")
        return
    
    try:
        client = create_client(url, key)
        
        # Try to list tables using information_schema
        # This is a more basic query that should work even with minimal permissions
        result = client.rpc('get_tables').execute()
        print(f"✓ Tables found: {result.data}")
        
    except Exception as e:
        print(f"❌ Error listing tables: {e}")
        print("\nAttempting to query specific tables...")
        
        # Try each expected table individually
        tables = ["agent_traces", "user_feedback", "project_context", "knowledge_relations"]
        
        for table in tables:
            try:
                result = client.table(table).select("count").limit(0).execute()
                print(f"   ✓ Table '{table}' exists")
            except Exception as table_error:
                if "relation" in str(table_error).lower() or "does not exist" in str(table_error).lower():
                    print(f"   ✗ Table '{table}' does NOT exist")
                else:
                    print(f"   ? Table '{table}': {table_error}")

if __name__ == "__main__":
    check_tables()
