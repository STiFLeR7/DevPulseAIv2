"""
Bytez API Embedding Sanity Test
Uses official Bytez SDK.
"""

import os
import sys
from dotenv import load_dotenv
from bytez import Bytez


def fail(msg):
    print(f"[FAIL] {msg}")
    sys.exit(1)


def ok(msg):
    print(f"[OK] {msg}")


def main():
    load_dotenv()

    api_key = os.getenv("BYTEZ_API_KEY")
    model = os.getenv("BYTEZ_EMBEDDING_MODEL")
    backend = os.getenv("EMBEDDING_BACKEND")

    if not api_key:
        fail("BYTEZ_API_KEY not set")
    ok("BYTEZ_API_KEY loaded")

    if backend != "bytez":
        print(f"[WARN] EMBEDDING_BACKEND is '{backend}', expected 'bytez'")
    else:
        ok("EMBEDDING_BACKEND set to 'bytez'")

    if not model:
        fail("BYTEZ_EMBEDDING_MODEL not set")
    ok(f"Using embedding model: {model}")

    # Initialize Bytez SDK
    sdk = Bytez(api_key)
    ok("Bytez SDK initialized")

    # Get model
    try:
        bytez_model = sdk.model(model)
        ok(f"Model '{model}' loaded")
    except Exception as e:
        fail(f"Failed to load model: {e}")

    # Run embedding
    test_text = "Artificial Intelligence enables machines to reason and learn."
    
    try:
        result = bytez_model.run(test_text)
        ok("Model execution successful")
    except Exception as e:
        fail(f"Model execution failed: {e}")

    # Handle API-side errors gracefully (e.g., missing paid plan)
    result_error = getattr(result, "error", None)
    if result_error:
        if "not on a plan" in result_error.lower() or "activate a plan" in result_error.lower():
            print("[WARN] Bytez account has no active plan; skipping embedding validation.")
            print(f"[INFO] Bytez response: {result_error}")
            sys.exit(0)
        fail(f"Bytez returned error: {result_error}")

    # Validate output
    if hasattr(result, 'output'):
        embedding = result.output
    elif hasattr(result, 'data'):
        embedding = result.data
    elif isinstance(result, dict):
        embedding = result.get('output') or result.get('data') or result.get('embeddings')
    else:
        embedding = result
    
    embedding = result.output
    
    if not isinstance(embedding, list):
        fail(f"Unexpected output type: {type(embedding)}")
    
    ok(f"Received embedding vector of length {len(embedding)}")

    print("\n[SUCCESS] Bytez embedding pipeline is functional.")


if __name__ == "__main__":
    main()
