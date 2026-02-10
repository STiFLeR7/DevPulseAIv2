import uuid
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from app.persistence.client import db

class Message:
    """Standardized communication protocol between agents."""
    def __init__(self, sender: str, recipient: str, content: str, metadata: Dict = None):
        self.id = str(uuid.uuid4())
        self.sender = sender
        self.recipient = recipient
        self.content = content
        self.metadata = metadata or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()

class Worker(ABC):
    """Base interface for all v3 agents."""
    
    def __init__(self, name: str):
        self.name = name
        self.run_id = None
        
    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the worker's specialized task."""
        pass
    
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
                # Silently fail if Supabase is not configured for testing
                pass

class SwarmManager:
    """Central orchestrator for the agent swarm."""
    
    def __init__(self):
        self.workers: Dict[str, Worker] = {}
        self.message_queue: List[Message] = []
        self.shared_context: Dict[str, Any] = {}
        
    def register_worker(self, worker: Worker):
        """Register a worker with the swarm."""
        self.workers[worker.name] = worker
        
    async def dispatch(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route a task to the appropriate worker.
        The task should contain a 'worker_type' field.
        """
        run_id = str(uuid.uuid4())
        worker_type = task.get("worker_type")
        
        if worker_type not in self.workers:
            return {
                "status": "error",
                "message": f"Worker '{worker_type}' not found"
            }
        
        worker = self.workers[worker_type]
        worker.run_id = run_id
        
        # Execute and capture result
        try:
            result = await worker.execute(task)
            worker.log_trace(
                step_name="dispatch_complete",
                input_state=task,
                output_state=result,
                status="completed"
            )
            return result
        except Exception as e:
            worker.log_trace(
                step_name="dispatch_failed",
                input_state=task,
                output_state={"error": str(e)},
                status="failed"
            )
            return {
                "status": "error",
                "message": str(e)
            }
    
    def send_message(self, message: Message):
        """Send a message between workers."""
        self.message_queue.append(message)
        
    def get_messages(self, recipient: str) -> List[Message]:
        """Get all messages for a specific worker."""
        return [m for m in self.message_queue if m.recipient == recipient]
