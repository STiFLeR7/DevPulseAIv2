
import os
import requests
from dotenv import load_dotenv
import json
import uuid

load_dotenv(override=True)

def verify_write_curl():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url.endswith("/rest/v1"):
        api_url = f"{url}/rest/v1/raw_signals"
    else:
        api_url = f"{url}/raw_signals"

    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    payload = {
        "source": "test_curl",
        "external_id": f"curl_{uuid.uuid4()}",
        "payload": {"foo": "bar"},
        "content_hash": "hash_123"
    }

    print(f"POST: {api_url}")
    try:
        resp = requests.post(api_url, headers=headers, json=payload)
        print(f"Status: {resp.status_code}")
        print(f"Body: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_write_curl()
