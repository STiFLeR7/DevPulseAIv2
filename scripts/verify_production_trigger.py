
import requests
import time

BASE_URL = "https://devpulse-ai-v2.onrender.com"

def verify_production():
    print(f"Checking {BASE_URL}...")
    
    # 1. Health Check (Get UI)
    try:
        resp = requests.get(BASE_URL)
        print(f"Root URL Status: {resp.status_code}") # Should be 200
    except Exception as e:
        print(f"Root URL Failed: {e}")
        return

    # 2. Trigger Daily Pulse
    print("Triggering /daily-pulse...")
    try:
        resp = requests.post(f"{BASE_URL}/daily-pulse")
        print(f"Trigger Status: {resp.status_code}")
        print(f"Response: {resp.text}")
        
        if resp.status_code == 200:
            print("SUCCESS: Production pipeline started! Check logs/email.")
        else:
            print("FAILURE: Endpoint returned error.")
            
    except Exception as e:
        print(f"Trigger Failed: {e}")

if __name__ == "__main__":
    verify_production()
