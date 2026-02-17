"""Test all Phase 3 API endpoints."""
import httpx
import sys

base = "http://localhost:8000"

def test_all():
    with httpx.Client(timeout=30) as c:
        # 1. Health
        print("--- /ping ---")
        r = c.get(f"{base}/ping")
        assert r.status_code == 200
        print(f"  OK: {r.json()}")

        # 2. Chat
        print("\n--- POST /api/chat ---")
        r = c.post(f"{base}/api/chat", json={"message": "Analyze pallets/flask"})
        assert r.status_code == 200
        d = r.json()
        conv_id = d["conversation_id"]
        print(f"  Conv ID: {conv_id}")
        print(f"  Response: {d['response'][:120]}...")

        # 3. Feedback
        print("\n--- POST /api/feedback ---")
        r = c.post(f"{base}/api/feedback", json={
            "conversation_id": conv_id,
            "vote_type": "positive",
            "message_preview": "Flask analysis"
        })
        assert r.status_code == 200
        print(f"  OK: {r.json()}")

        # 4. Signals
        print("\n--- GET /api/signals ---")
        r = c.get(f"{base}/api/signals?limit=2")
        assert r.status_code == 200
        print(f"  Count: {len(r.json())}")

        # 5. Intelligence
        print("\n--- GET /api/intelligence ---")
        r = c.get(f"{base}/api/intelligence?limit=2")
        assert r.status_code == 200
        print(f"  Count: {len(r.json())}")

        # 6. Conversations
        print(f"\n--- GET /api/conversations/{conv_id[:8]}... ---")
        r = c.get(f"{base}/api/conversations/{conv_id}?limit=5")
        assert r.status_code == 200
        print(f"  Messages: {len(r.json())}")

        # 7. Recommendations
        print("\n--- GET /api/recommendations ---")
        r = c.get(f"{base}/api/recommendations?limit=3")
        assert r.status_code == 200
        recs = r.json()
        print(f"  Recs: {len(recs)}")
        for rec in recs[:2]:
            print(f"    [{rec.get('type')}] {rec.get('content','')[:60]}")

    print("\n=== ALL 7 ENDPOINT TESTS PASSED ===")

if __name__ == "__main__":
    test_all()
