import os
import sys
from dotenv import load_dotenv
sys.path.append(os.getcwd())
load_dotenv(override=True)

from app.persistence.client import db

def test_insert():
    print("--- Testing DB Insert ---")
    try:
        data = db.insert_raw_signal(
            source="test_debug",
            external_id="12345",
            payload={"title": "Test Signal", "content": "Just a test."},
            content_hash="dummy_hash_123"
        )
        if data:
            print(f"✅ Insert Successful: ID {data['id']}")
        else:
            print("❌ Insert returned None (Silent Failure?)")
    except Exception as e:
        print(f"❌ Insert Exception: {e}")
        if hasattr(e, '__dict__'):
            print(f"Details: {e.__dict__}")

if __name__ == "__main__":
    test_insert()
