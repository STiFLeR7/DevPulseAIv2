"""
MultiSwarm Orchestration Engine for DevPulseAI v3

Inspired by KimiK2.5's Agent Swarm paradigm:
- Dynamic sub-agent spawning and coordination
- Parallel task decomposition and execution
- Self-directed routing with a Coordinator pattern
- Inter-agent messaging protocol

Architecture:
  ┌─────────────────────────────────────────────┐
  │              MultiSwarmManager               │
  │  ┌─────────┐  ┌─────────┐  ┌─────────────┐ │
  │  │  Swarm   │  │  Swarm   │  │   Swarm     │ │
  │  │ (Research)│  │ (Analysis)│ │ (General)   │ │
  │  │ ┌──────┐ │  │ ┌──────┐ │  │ ┌─────────┐│ │
  │  │ │Worker│ │  │ │Worker│ │  │ │  Worker  ││ │
  │  │ │Worker│ │  │ │Worker│ │  │ │  Worker  ││ │
  │  │ └──────┘ │  │ └──────┘ │  │ └─────────┘│ │
  │  └─────────┘  └─────────┘  └─────────────┘ │
  │           ↕ Message Bus ↕                    │
  └─────────────────────────────────────────────┘
"""

import uuid
import asyncio
from typing import Dict, List, Any, Optional, Callable
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum

from app.persistence.client import db


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Message Protocol
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class MessageType(Enum):
    """Types of inter-agent messages."""
    TASK = "task"
    RESULT = "result"
    QUERY = "query"
    BROADCAST = "broadcast"
    HEARTBEAT = "heartbeat"


class Message:
    """Standardized communication protocol between agents."""
    
    def __init__(self, sender: str, recipient: str, content: str,
                 msg_type: MessageType = MessageType.TASK, metadata: Dict = None):
        self.id = str(uuid.uuid4())
        self.sender = sender
        self.recipient = recipient
        self.content = content
        self.msg_type = msg_type
        self.metadata = metadata or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "sender": self.sender,
            "recipient": self.recipient,
            "content": self.content,
            "type": self.msg_type.value,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Worker Base Class
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Worker(ABC):
    """
    Base interface for all v3 agents.
    
    Each worker is a specialized unit that can:
    - Execute tasks independently
    - Communicate via the message bus
    - Log execution traces to Supabase
    """
    
    def __init__(self, name: str, capabilities: List[str] = None):
        self.name = name
        self.capabilities = capabilities or []
        self.run_id = None
        self.status = "idle"  # idle, busy, error
        
    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the worker's specialized task."""
        pass
    
    def can_handle(self, task_type: str) -> bool:
        """Check if this worker can handle a given task type."""
        return task_type in self.capabilities
    
    def log_trace(self, step_name: str, input_state: Dict, output_state: Dict, status: str = "completed"):
        """Log execution trace to Supabase."""
        if self.run_id:
            try:
                db.log_trace(
                    run_id=self.run_id,
                    agent_name=self.name,
                    step_name=step_name,
                    input_state=input_state,
                    output_state=output_state,
                    status=status
                )
            except Exception:
                pass  # Silent fail for testing


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Swarm (Group of Workers)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Swarm:
    """
    A logical group of related workers.
    
    Each swarm manages a domain of expertise (e.g., Research, Analysis).
    Workers within a swarm can be dispatched in parallel.
    """
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.workers: Dict[str, Worker] = {}
    
    def add_worker(self, worker: Worker):
        """Add a worker to this swarm."""
        self.workers[worker.name] = worker
    
    def get_worker(self, name: str) -> Optional[Worker]:
        """Get a specific worker by name."""
        return self.workers.get(name)
    
    def list_workers(self) -> List[str]:
        """List all worker names in this swarm."""
        return list(self.workers.keys())
    
    def find_capable_worker(self, task_type: str) -> Optional[Worker]:
        """Find a worker that can handle the given task type."""
        for worker in self.workers.values():
            if worker.can_handle(task_type):
                return worker
        return None

    async def dispatch(self, worker_name: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch a task to a specific worker in this swarm."""
        worker = self.get_worker(worker_name)
        if not worker:
            return {"status": "error", "summary": f"Worker '{worker_name}' not found in swarm '{self.name}'"}
        
        run_id = str(uuid.uuid4())
        worker.run_id = run_id
        worker.status = "busy"
        
        try:
            result = await worker.execute(task)
            worker.status = "idle"
            return result
        except Exception as e:
            worker.status = "error"
            return {"status": "error", "summary": str(e)}
    
    async def dispatch_parallel(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        KimiK2.5-style parallel dispatch.
        Run multiple tasks across available workers simultaneously.
        """
        coroutines = []
        for task in tasks:
            worker_name = task.get("worker_name")
            if worker_name and worker_name in self.workers:
                coroutines.append(self.dispatch(worker_name, task))
        
        if coroutines:
            return await asyncio.gather(*coroutines, return_exceptions=True)
        return []


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MultiSwarm Manager (The Coordinator)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class SwarmManager:
    """
    Central orchestrator for the multi-swarm system.
    
    Implements KimiK2.5's Agent Swarm paradigm:
    - Manages multiple swarms, each specialized in a domain
    - Dynamic task decomposition and routing
    - Parallel execution across swarms
    - Inter-swarm message bus for coordination
    
    Usage:
        manager = SwarmManager()
        
        # Create domain swarms
        research_swarm = manager.create_swarm("research", "GitHub & code analysis")
        analysis_swarm = manager.create_swarm("analysis", "Paper & data analysis")
        
        # Add workers
        research_swarm.add_worker(RepoResearcher())
        analysis_swarm.add_worker(PaperAnalyst())
        
        # Direct worker access
        worker = manager.get_worker("RepoResearcher")
        
        # Or dispatch via the manager
        result = await manager.dispatch("RepoResearcher", task)
    """
    
    def __init__(self):
        self.swarms: Dict[str, Swarm] = {}
        self.worker_registry: Dict[str, str] = {}  # worker_name -> swarm_name
        self.message_bus: List[Message] = []
        self.shared_context: Dict[str, Any] = {}
        self.execution_log: List[Dict] = []
    
    # ── Swarm Management ──────────────────────────
    
    def create_swarm(self, name: str, description: str = "") -> Swarm:
        """Create and register a new swarm."""
        swarm = Swarm(name=name, description=description)
        self.swarms[name] = swarm
        return swarm
    
    def get_swarm(self, name: str) -> Optional[Swarm]:
        """Get a swarm by name."""
        return self.swarms.get(name)
    
    def list_swarms(self) -> Dict[str, List[str]]:
        """List all swarms and their workers."""
        return {
            name: swarm.list_workers()
            for name, swarm in self.swarms.items()
        }
    
    # ── Worker Management ─────────────────────────
    
    def register_worker(self, worker: Worker, swarm_name: str = "default"):
        """
        Register a worker into a swarm.
        Creates the swarm if it doesn't exist.
        """
        if swarm_name not in self.swarms:
            self.create_swarm(swarm_name, f"Auto-created swarm for {swarm_name}")
        
        self.swarms[swarm_name].add_worker(worker)
        self.worker_registry[worker.name] = swarm_name
    
    def get_worker(self, name: str) -> Optional[Worker]:
        """
        Get any worker by name, regardless of which swarm it belongs to.
        This is the key method that was missing!
        """
        swarm_name = self.worker_registry.get(name)
        if swarm_name and swarm_name in self.swarms:
            return self.swarms[swarm_name].get_worker(name)
        return None
    
    def find_worker_for_task(self, task_type: str) -> Optional[Worker]:
        """Find any worker across all swarms that can handle this task type."""
        for swarm in self.swarms.values():
            worker = swarm.find_capable_worker(task_type)
            if worker:
                return worker
        return None
    
    # ── Task Dispatch ─────────────────────────────
    
    async def dispatch(self, worker_name: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatch a task to a specific worker.
        Finds the worker across all swarms and executes.
        """
        swarm_name = self.worker_registry.get(worker_name)
        if not swarm_name:
            return {"status": "error", "summary": f"Worker '{worker_name}' not registered"}
        
        swarm = self.swarms.get(swarm_name)
        if not swarm:
            return {"status": "error", "summary": f"Swarm '{swarm_name}' not found"}
        
        # Log execution
        self.execution_log.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "worker": worker_name,
            "swarm": swarm_name,
            "task_type": task.get("intent", "unknown")
        })
        
        return await swarm.dispatch(worker_name, task)
    
    async def dispatch_parallel(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        KimiK2.5-style parallel multi-swarm dispatch.
        
        Decomposes tasks and runs them across multiple swarms simultaneously.
        Each task dict should contain 'worker_name' to route to the right worker.
        """
        coroutines = []
        for task in tasks:
            worker_name = task.get("worker_name")
            if worker_name:
                coroutines.append(self.dispatch(worker_name, task))
        
        if coroutines:
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            # Convert exceptions to error dicts
            processed = []
            for r in results:
                if isinstance(r, Exception):
                    processed.append({"status": "error", "summary": str(r)})
                else:
                    processed.append(r)
            return processed
        return []
    
    async def fan_out(self, task: Dict[str, Any], worker_names: List[str]) -> List[Dict[str, Any]]:
        """
        Fan-out a single task to multiple workers simultaneously.
        Useful for getting multiple perspectives on the same query.
        """
        tasks = [{**task, "worker_name": name} for name in worker_names]
        return await self.dispatch_parallel(tasks)
    
    # ── Message Bus ───────────────────────────────
    
    def send_message(self, message: Message):
        """Send a message on the inter-swarm bus."""
        self.message_bus.append(message)
    
    def get_messages(self, recipient: str) -> List[Message]:
        """Get all messages for a specific worker."""
        return [m for m in self.message_bus if m.recipient == recipient]
    
    def broadcast(self, sender: str, content: str, metadata: Dict = None):
        """Broadcast a message to all workers across all swarms."""
        for swarm in self.swarms.values():
            for worker_name in swarm.list_workers():
                msg = Message(
                    sender=sender,
                    recipient=worker_name,
                    content=content,
                    msg_type=MessageType.BROADCAST,
                    metadata=metadata
                )
                self.message_bus.append(msg)
    
    # ── Shared Context ────────────────────────────
    
    def set_context(self, key: str, value: Any):
        """Set shared context accessible by all workers."""
        self.shared_context[key] = value
    
    def get_context(self, key: str) -> Any:
        """Get shared context value."""
        return self.shared_context.get(key)
    
    # ── Diagnostics ───────────────────────────────
    
    def status(self) -> Dict:
        """Get full system status."""
        return {
            "swarms": {
                name: {
                    "workers": swarm.list_workers(),
                    "worker_count": len(swarm.workers)
                }
                for name, swarm in self.swarms.items()
            },
            "total_workers": len(self.worker_registry),
            "message_queue_size": len(self.message_bus),
            "executions": len(self.execution_log)
        }
