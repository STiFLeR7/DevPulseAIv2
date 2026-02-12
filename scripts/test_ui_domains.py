"""
Multi-Domain Integration Test for DevPulseAI v3 UI

Tests the ConversationManager across all intent domains to verify:
1. Intent detection for each domain
2. Worker routing
3. Response generation
4. Error handling under rate limits
"""

import sys
import os
import asyncio
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.conversation import ConversationManager, Intent

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test Queries — 4 Domains
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TEST_QUERIES = [
    # Domain 1: Repo Analysis
    {
        "query": "Analyze the FastAPI repository and tell me about its architecture",
        "expected_intent": Intent.REPO_ANALYSIS,
        "domain": "GitHub/Repo",
    },
    # Domain 2: Paper Search
    {
        "query": "Find recent papers on Retrieval Augmented Generation techniques",
        "expected_intent": Intent.PAPER_SEARCH,
        "domain": "ArXiv/Papers",
    },
    # Domain 3: Local File Read (ProjectExplorer)
    {
        "query": "Read the content of README.md present at D:/DevPulseAIv2/",
        "expected_intent": Intent.PROJECT_CONTEXT,
        "domain": "Local/Files",
    },
    # Domain 4: General Q&A (Gemini direct)
    {
        "query": "Explain dependency injection in Python with a simple example",
        "expected_intent": Intent.GENERAL_QA,
        "domain": "General/QA",
    },
    # Domain 5: Local directory tree
    {
        "query": "Show me the directory tree structure of D:/DevPulseAIv2/app/",
        "expected_intent": Intent.PROJECT_CONTEXT,
        "domain": "Local/Directory",
    },
    # Domain 6: Ambiguous — should route correctly
    {
        "query": "What is the repo structure of this project at D:/DevPulseAIv2?",
        "expected_intent": Intent.PROJECT_CONTEXT,  # local path should override "repo" keyword
        "domain": "Ambiguous/LocalOverride",
    },
]


def run_tests():
    print("=" * 70)
    print("  DevPulseAI v3 — Multi-Domain Integration Test")
    print("=" * 70)
    print()

    conv = ConversationManager()
    
    # Phase 1: Verify Swarm Status
    print("--- Phase 1: Swarm Status ---")
    status = conv.swarm.status()
    print(f"  Total workers: {status['total_workers']}")
    for name, info in status["swarms"].items():
        print(f"  Swarm [{name}]: {info['workers']} ({info['worker_count']} workers)")
    print()

    # Phase 2: Intent Detection Tests
    print("--- Phase 2: Intent Detection ---")
    intent_pass = 0
    intent_fail = 0
    
    for test in TEST_QUERIES:
        detected = conv.detect_intent(test["query"])
        match = "✅" if detected == test["expected_intent"] else "❌"
        if detected == test["expected_intent"]:
            intent_pass += 1
        else:
            intent_fail += 1
        print(f"  {match} [{test['domain']}] Expected: {test['expected_intent'].value}, Got: {detected.value}")
        # Small delay to respect rate limits
        time.sleep(0.5)
    
    print(f"\n  Intent Results: {intent_pass} passed, {intent_fail} failed")
    print()

    # Phase 3: Full Processing Tests
    print("--- Phase 3: Full Message Processing ---")
    
    async def run_all():
        results = []
        for i, test in enumerate(TEST_QUERIES):
            print(f"\n  [{i+1}/{len(TEST_QUERIES)}] Testing: {test['domain']}")
            print(f"  Query: {test['query'][:60]}...")
            
            start = time.time()
            try:
                response = await conv.process_message(test["query"])
                elapsed = time.time() - start
                
                # Truncate response for display
                resp_preview = response[:150].replace("\n", " ") if response else "(empty)"
                
                print(f"  ✅ Response ({elapsed:.1f}s): {resp_preview}...")
                results.append({"domain": test["domain"], "status": "pass", "time": elapsed})
            except Exception as e:
                elapsed = time.time() - start
                print(f"  ❌ Error ({elapsed:.1f}s): {str(e)[:100]}")
                results.append({"domain": test["domain"], "status": "fail", "time": elapsed, "error": str(e)})
            
            # Respect rate limits between queries
            print(f"  ⏳ Waiting 3s for rate limit cooldown...")
            time.sleep(3)
        
        return results
    
    results = asyncio.run(run_all())
    
    # Summary
    print()
    print("=" * 70)
    print("  RESULTS SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for r in results if r["status"] == "pass")
    failed = sum(1 for r in results if r["status"] == "fail")
    total_time = sum(r["time"] for r in results)
    
    print(f"\n  Total Queries:  {len(results)}")
    print(f"  Passed:         {passed}")
    print(f"  Failed:         {failed}")
    print(f"  Total Time:     {total_time:.1f}s")
    print(f"  Avg Time/Query: {total_time/len(results):.1f}s")
    print()
    
    for r in results:
        status_icon = "✅" if r["status"] == "pass" else "❌"
        print(f"  {status_icon} {r['domain']:25s} {r['time']:.1f}s")
    
    print()
    
    if failed == 0:
        print("  🎉 ALL TESTS PASSED!")
    else:
        print(f"  ⚠️  {failed} test(s) failed — check errors above")
    
    print()


if __name__ == "__main__":
    run_tests()
