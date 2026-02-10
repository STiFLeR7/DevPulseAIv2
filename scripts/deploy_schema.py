import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def deploy_schema():
    """Deploy the schema to Supabase."""
    print("="*60)
    print("Deploying DevPulseAI v3 Schema to Supabase")
    print("="*60)
    
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        print("❌ Missing SUPABASE_URL or SUPABASE_KEY")
        return False
    
    # Read schema file
    schema_path = os.path.join(os.path.dirname(__file__), "..", "app", "persistence", "schema.sql")
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    print(f"\n1. Schema file loaded: {schema_path}")
    print(f"   SQL length: {len(schema_sql)} bytes")
    
    # Create client
    try:
        client = create_client(url, key)
        print("\n2. Supabase client connected")
        
        # Execute schema
        print("\n3. Executing schema SQL...")
        result = client.rpc('exec_sql', {'query': schema_sql}).execute()
        print("   ✓ Schema executed successfully!")
        
        return True
        
    except Exception as e:
        error_str = str(e)
        if "does not exist" in error_str and "exec_sql" in error_str:
            print("\n❌ The 'exec_sql' RPC function doesn't exist.")
            print("\n📋 Manual deployment required:")
            print("   1. Go to Supabase Dashboard → SQL Editor")
            print(f"   2. Project URL: {url}")
            print("   3. Copy contents of: app/persistence/schema.sql")
            print("   4. Paste and run in SQL Editor")
            return False
        else:
            print(f"\n❌ Error executing schema: {e}")
            return False

if __name__ == "__main__":
    success = deploy_schema()
    if success:
        print("\n✅ Schema deployment complete!")
    else:
        print("\n⚠️  Please deploy schema manually via Supabase Dashboard")
