"""
Comprehensive End-to-End Test — ArXiv, GitHub, Supabase, Pinecone
"""

import sys, asyncio, time
sys.path.insert(0, ".")

from app.core.conversation import ConversationManager
from app.persistence.client import db


def count_rows(table: str) -> int:
    try:
        result = db.get_client().table(table).select("id", count="exact").execute()
        return result.count if result.count is not None else len(result.data)
    except Exception as e:
        print(f"  Warning: {table}: {e}")
        return -1


def show_recent_rows(table: str, n: int = 3):
    """Show the N most recent rows from a table."""
    try:
        result = db.get_client().table(table).select("*").order("created_at", desc=True).limit(n).execute()
        if result.data:
            for row in result.data:
                # Show a summary of each row
                preview = str(row)[:200]
                print(f"    -> {preview}...")
        else:
            print(f"    (empty)")
    except Exception as e:
        print(f"    Error: {e}")


def main():
    print("=" * 70)
    print("  DevPulseAI v3 -- FULL Integration Test")
    print("  Tests: GitHub API + ArXiv API + Supabase + Pinecone")
    print("=" * 70)

    # Snapshot BEFORE
    tables = ["conversations", "audit_logs", "raw_signals", "processed_intelligence", "agent_traces"]
    print("\n--- BEFORE ---")
    before = {}
    for t in tables:
        before[t] = count_rows(t)
        print(f"  {t}: {before[t]}")

    conv = ConversationManager()

    test_cases = [
        {
            "query": "Analyze the repository pallets/flask",
            "expected_intent": "repo_analysis",
            "real_check": lambda r: "Stars" in r or "stars" in r.lower() or "flask" in r.lower(),
        },
        {
            "query": "Find papers on transformer attention mechanism",
            "expected_intent": "paper_search",
            "real_check": lambda r: "ArXiv" in r or "arxiv" in r or "Authors" in r,
        },
        {
            "query": "What is retrieval augmented generation?",
            "expected_intent": "general_qa",
            "real_check": lambda r: len(r) > 50,
        },
    ]

    async def run_tests():
        results = []
        for tc in test_cases:
            q = tc["query"]
            print(f"\n  QUERY: {q}")
            start = time.time()
            try:
                resp = await conv.process_message(q)
                elapsed = time.time() - start
                is_real = tc["real_check"](resp)
                status = "REAL" if is_real else "MOCK"
                print(f"  [{status}] ({elapsed:.1f}s) {resp[:150].replace(chr(10), ' ')}...")
                results.append({"query": q, "real": is_real, "time": elapsed})
            except Exception as e:
                elapsed = time.time() - start
                print(f"  [ERROR] ({elapsed:.1f}s) {str(e)[:100]}")
                results.append({"query": q, "real": False, "time": elapsed})
            time.sleep(2)
        return results

    results = asyncio.run(run_tests())

    # Snapshot AFTER
    print("\n\n--- AFTER ---")
    after = {}
    for t in tables:
        after[t] = count_rows(t)
        diff = after[t] - before[t]
        icon = "+" if diff > 0 else ""
        print(f"  {t}: {after[t]} ({icon}{diff})")

    # Show recent data from each table
    print("\n--- LATEST DATA IN SUPABASE ---")
    for t in tables:
        print(f"\n  [{t}] (most recent 2 rows):")
        show_recent_rows(t, 2)

    # Results summary
    print("\n" + "=" * 70)
    print("  RESULTS SUMMARY")
    print("=" * 70)

    checks = {
        "Conversations persisted":  after["conversations"]  > before["conversations"],
        "Audit logs persisted":     after["audit_logs"]      > before["audit_logs"],
        "Raw signals persisted":    after["raw_signals"]     > before["raw_signals"],
        "Intelligence persisted":   after["processed_intelligence"] > before["processed_intelligence"],
        "Agent traces persisted":   after["agent_traces"]    > before["agent_traces"],
        "GitHub returns REAL data": results[0]["real"],
        "ArXiv returns REAL data":  results[1]["real"],
        "Gemini returns REAL data": results[2]["real"],
    }

    all_pass = True
    for check, passed in checks.items():
        icon = "PASS" if passed else "FAIL"
        print(f"  [{icon}] {check}")
        if not passed:
            all_pass = False

    print()
    if all_pass:
        print("  >>> ALL CHECKS PASSED! <<<")
    else:
        print("  Some checks failed. See above.")
    print()


if __name__ == "__main__":
    main()
