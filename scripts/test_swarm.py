"""
Tests for the MultiSwarm Orchestration Engine.

Verifies:
- Worker registration into swarms
- get_worker across swarms
- Single dispatch
- Parallel dispatch (KimiK2.5 style)
- Fan-out queries
- Message bus
"""

import asyncio
import sys
import warnings
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Suppress Supabase deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from app.core.swarm import SwarmManager, Worker, Message, MessageType, Swarm


class MockResearcher(Worker):
    """Mock worker simulating RepoResearcher."""
    def __init__(self):
        super().__init__(name="MockResearcher", capabilities=["repo_analysis"])
        self.executed = False
        
    async def execute(self, task: dict) -> dict:
        self.executed = True
        return {"status": "success", "summary": f"Analyzed repo from: {task.get('user_message', 'N/A')}"}


class MockAnalyst(Worker):
    """Mock worker simulating PaperAnalyst."""
    def __init__(self):
        super().__init__(name="MockAnalyst", capabilities=["paper_search"])
        self.executed = False
        
    async def execute(self, task: dict) -> dict:
        self.executed = True
        return {"status": "success", "summary": f"Found papers on: {task.get('user_message', 'N/A')}"}


class MockCritic(Worker):
    """Mock worker simulating CriticAgent."""
    def __init__(self):
        super().__init__(name="MockCritic", capabilities=["validation"])
        self.executed = False
        
    async def execute(self, task: dict) -> dict:
        self.executed = True
        return {"status": "success", "summary": "Validation passed"}


async def test_multiswarm():
    """Test the full multiswarm system."""
    
    print("=" * 60)
    print("  MultiSwarm Orchestration Engine Tests")
    print("=" * 60)
    
    manager = SwarmManager()
    
    # ── Test 1: Create swarms ─────────────────────
    print("\n[TEST 1] Creating domain swarms...")
    research_swarm = manager.create_swarm("research", "Code & repo analysis")
    analysis_swarm = manager.create_swarm("analysis", "Paper & data analysis")
    
    assert "research" in manager.swarms
    assert "analysis" in manager.swarms
    print("  ✅ Swarms created: research, analysis")
    
    # ── Test 2: Register workers into swarms ──────
    print("\n[TEST 2] Registering workers into swarms...")
    researcher = MockResearcher()
    analyst = MockAnalyst()
    critic = MockCritic()
    
    manager.register_worker(researcher, swarm_name="research")
    manager.register_worker(analyst, swarm_name="analysis")
    manager.register_worker(critic, swarm_name="research")  # Critic in research swarm
    
    assert len(manager.worker_registry) == 3
    print(f"  ✅ Registered {len(manager.worker_registry)} workers")
    print(f"     Research: {research_swarm.list_workers()}")
    print(f"     Analysis: {analysis_swarm.list_workers()}")
    
    # ── Test 3: get_worker (THE BUG FIX) ──────────
    print("\n[TEST 3] Testing get_worker (the original bug fix)...")
    worker = manager.get_worker("MockResearcher")
    assert worker is not None
    assert worker.name == "MockResearcher"
    
    worker2 = manager.get_worker("MockAnalyst")
    assert worker2 is not None
    
    missing = manager.get_worker("NonExistent")
    assert missing is None
    
    print("  ✅ get_worker works across swarms")
    
    # ── Test 4: Single dispatch ───────────────────
    print("\n[TEST 4] Testing single dispatch...")
    result = await manager.dispatch("MockResearcher", {"user_message": "analyze tiangolo/fastapi"})
    assert result["status"] == "success"
    assert "Analyzed repo" in result["summary"]
    assert researcher.executed
    print(f"  ✅ Dispatch result: {result['summary']}")
    
    # ── Test 5: Parallel dispatch (KimiK2.5) ──────
    print("\n[TEST 5] Testing KimiK2.5-style parallel dispatch...")
    tasks = [
        {"worker_name": "MockResearcher", "user_message": "analyze langchain-ai/langchain"},
        {"worker_name": "MockAnalyst", "user_message": "find papers on RAG"},
    ]
    results = await manager.dispatch_parallel(tasks)
    assert len(results) == 2
    assert all(r.get("status") == "success" for r in results)
    print(f"  ✅ Parallel dispatch: {len(results)} tasks completed simultaneously")
    for r in results:
        print(f"     → {r['summary']}")
    
    # ── Test 6: Fan-out ───────────────────────────
    print("\n[TEST 6] Testing fan-out (same task to multiple workers)...")
    fan_results = await manager.fan_out(
        {"user_message": "What is RAG?"},
        ["MockResearcher", "MockAnalyst"]
    )
    assert len(fan_results) == 2
    print(f"  ✅ Fan-out: {len(fan_results)} perspectives collected")
    
    # ── Test 7: Message bus ───────────────────────
    print("\n[TEST 7] Testing inter-swarm message bus...")
    msg = Message(
        sender="MockResearcher",
        recipient="MockAnalyst",
        content="Found interesting repo, needs paper analysis",
        msg_type=MessageType.QUERY
    )
    manager.send_message(msg)
    
    received = manager.get_messages("MockAnalyst")
    assert len(received) == 1
    assert received[0].content == "Found interesting repo, needs paper analysis"
    print(f"  ✅ Message delivered: {received[0].sender} → {received[0].recipient}")
    
    # ── Test 8: Broadcast ─────────────────────────
    print("\n[TEST 8] Testing broadcast...")
    manager.broadcast("system", "New project context loaded")
    
    researcher_msgs = manager.get_messages("MockResearcher")
    analyst_msgs = manager.get_messages("MockAnalyst")
    assert len(researcher_msgs) >= 1
    assert len(analyst_msgs) >= 2  # 1 direct + 1 broadcast
    print(f"  ✅ Broadcast delivered to all workers")
    
    # ── Test 9: Shared context ────────────────────
    print("\n[TEST 9] Testing shared context...")
    manager.set_context("project_name", "DevPulseAI")
    manager.set_context("tech_stack", ["Python", "Streamlit", "Supabase"])
    
    assert manager.get_context("project_name") == "DevPulseAI"
    assert len(manager.get_context("tech_stack")) == 3
    print(f"  ✅ Shared context: {manager.get_context('project_name')}")
    
    # ── Test 10: System status ────────────────────
    print("\n[TEST 10] System status...")
    status = manager.status()
    assert status["total_workers"] == 3
    assert len(status["swarms"]) == 2
    print(f"  ✅ System status:")
    print(f"     Swarms: {list(status['swarms'].keys())}")
    print(f"     Total workers: {status['total_workers']}")
    print(f"     Executions logged: {status['executions']}")
    
    # ── Test 11: find_worker_for_task ──────────────
    print("\n[TEST 11] Testing capability-based worker discovery...")
    found = manager.find_worker_for_task("repo_analysis")
    assert found is not None
    assert found.name == "MockResearcher"
    
    found2 = manager.find_worker_for_task("paper_search")
    assert found2 is not None
    assert found2.name == "MockAnalyst"
    
    not_found = manager.find_worker_for_task("flying_cars")
    assert not_found is None
    print(f"  ✅ Capability-based discovery working")
    
    print("\n" + "=" * 60)
    print("  ✅ ALL 11 TESTS PASSED — MultiSwarm is operational!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_multiswarm())
