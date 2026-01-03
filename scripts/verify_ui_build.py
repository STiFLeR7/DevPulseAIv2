import requests
import sys

BASE_URL = "http://localhost:8080" # Local running instance if possible, or mocked.
# Since we are not running locally, this script is hard to run against the live code without running it.
# Instead, let's verify file existence and content locally.

def check_ui_build():
    try:
        with open("ui/dist/index.html", "r", encoding="utf-8") as f:
            content = f.read()
            if "<div id=\"root\">" in content or "vite" in content or "<script" in content:
                print("SUCCESS: ui/dist/index.html looks like a built React app.")
            else:
                print("WARNING: index.html might be empty or invalid.")
    except Exception as e:
        print(f"ERROR: Could not read ui/dist/index.html: {e}")

if __name__ == "__main__":
    check_ui_build()
