import os
from dotenv import load_dotenv

# Force reload of .env
load_dotenv(override=True)

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

print(f"URL: {url}")
print(f"Key: {key[:50]}...")
print(f"\nKey role check:")
if "anon" in key:
    print("✓ Anon key detected")
elif "service_role" in key:
    print("✗ Service role key detected")
else:
    print("? Unknown key type")

# Decode JWT to see what's inside
import json
import base64

def decode_jwt(token):
    # Split the JWT
    parts = token.split('.')
    if len(parts) != 3:
        return "Invalid JWT"
    
    # Decode the payload (second part)
    payload = parts[1]
    # Add padding if necessary
    padding = 4 - len(payload) % 4
    if padding:
        payload += '=' * padding
    
    decoded = base64.urlsafe_b64decode(payload)
    return json.loads(decoded)

payload = decode_jwt(key)
print(f"\nJWT Payload: {json.dumps(payload, indent=2)}")
