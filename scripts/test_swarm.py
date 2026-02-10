import sys
import os
import unittest
import asyncio
import warnings
from unittest.mock import MagicMock, AsyncMock

# Suppress deprecation warnings from Supabase client
warnings.filterwarnings("ignore", category=DeprecationWarning, module="supabase")

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.swarm import SwarmManager, Worker, Message

class MockWorker(Worker):
    """Mock worker for testing."""
    def __init__(self, name: str):
        super().__init__(name=name)
        self.executed = False
        
    async def execute(self, task: dict) -> dict:
        """Override abstract execute method."""
        self.executed = True
        return {"status": "success", "result": "mock_output"}

class TestSwarmManager(unittest.TestCase):
    
    def setUp(self):
        self.swarm = SwarmManager()
        self.mock_worker = MockWorker("test_worker")
        
    def test_register_worker(self):
        self.swarm.register_worker(self.mock_worker)
        self.assertIn("test_worker", self.swarm.workers)
        self.assertEqual(self.swarm.workers["test_worker"], self.mock_worker)
    
    def test_dispatch_success(self):
        self.swarm.register_worker(self.mock_worker)
        
        task = {
            "worker_type": "test_worker",
            "data": "test_data"
        }
        
        result = asyncio.run(self.swarm.dispatch(task))
        
        self.assertEqual(result["status"], "success")
        self.assertTrue(self.mock_worker.executed)
    
    def test_dispatch_worker_not_found(self):
        task = {
            "worker_type": "nonexistent_worker",
            "data": "test_data"
        }
        
        result = asyncio.run(self.swarm.dispatch(task))
        
        self.assertEqual(result["status"], "error")
        self.assertIn("not found", result["message"])
    
    def test_message_queue(self):
        msg = Message(
            sender="worker1",
            recipient="worker2",
            content="test message"
        )
        
        self.swarm.send_message(msg)
        messages = self.swarm.get_messages("worker2")
        
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].content, "test message")

if __name__ == "__main__":
    unittest.main()
