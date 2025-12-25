
import os
import requests
from dotenv import load_dotenv
import json

load_dotenv(override=True)

def verify_curl():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        print("Missing URL/KEY")
        return

    # normalize URL
    if not url.endswith("/rest/v1"):
        api_url = f"{url}/rest/v1/raw_signals?select=id&limit=1"
    else:
        api_url = f"{url}/raw_signals?select=id&limit=1"

    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

    print(f"Requesting: {api_url}")
    try:
        resp = requests.get(api_url, headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Raw Body: {resp.text}")
        
        try:
            print("Parsed JSON:", resp.json())
        except:
            print("Body is not JSON.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_curl()
