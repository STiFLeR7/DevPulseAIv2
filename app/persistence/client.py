import os
import hashlib
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class SupabaseManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseManager, cls).__new__(cls)
            cls._instance._init_client()
        return cls._instance

    def _init_client(self):
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")
        
        if not url or not key:
            # We don't raise error immediately to allow tests to mock, 
            # but in production this strictly required.
            print("WARNING: SUPABASE_URL or SUPABASE_KEY not set.")
            self.client = None
            return

        self.client: Client = create_client(url, key)

    def get_client(self) -> Client:
        if not self.client:
            raise ValueError("Supabase client is not initialized. Check environment variables.")
        return self.client

    def insert_raw_signal(self, source: str, external_id: str, payload: dict, content_hash: str):
        """
        Inserts a raw signal if it doesn't exist.
        """
        data = {
            "source": source,
            "external_id": external_id,
            "payload": payload,
            "content_hash": content_hash
        }
        # using upsert or ignore constraint could be better, but for now specific check or error handling 
        # is delegated to the caller or handled by unique constraints.
        response = self.get_client().table("raw_signals").upsert(data, on_conflict="source, external_id").execute()
        if response.data:
            return response.data[0] # Return the first (and only) record
        return None

    
    def insert_intelligence(self, signal_id: str, agent_name: str, agent_version: str, output_data: dict):
        """
        Stores processed intelligence.
        """
        data = {
            "signal_id": signal_id,
            "agent_name": agent_name,
            "agent_version": agent_version,
            "output_data": output_data
        }
        return self.get_client().table("processed_intelligence").upsert(
            data, on_conflict="signal_id, agent_name, agent_version"
        ).execute()

    def log_event(self, component: str, event_type: str, message: str, metadata: dict = None):
        """
        Writes to audit_logs.
        """
        data = {
            "component": component,
            "event_type": event_type,
            "message": message,
            "metadata": metadata or {}
        }
        try:
            return self.get_client().table("audit_logs").insert(data).execute()
        except Exception as e:
            # Fallback to stdout if logging fails
            print(f"FAILED TO LOG TO DB: {e}")

    def log_trace(self, run_id: str, agent_name: str, step_name: str, input_state: dict, output_state: dict, tool_calls: list = None, model_name: str = None, status: str = "completed", error_message: str = None):
        """
        Logs an agent execution step for observability.
        """
        data = {
            "run_id": run_id,
            "agent_name": agent_name,
            "step_name": step_name,
            "input_state": input_state,
            "output_state": output_state,
            "tool_calls": tool_calls or [],
            "model_name": model_name,
            "status": status,
            "error_message": error_message
        }
        try:
            return self.get_client().table("agent_traces").insert(data).execute()
        except Exception as e:
            # Silently fail - caller will handle if needed
            raise

    def save_feedback(self, signal_id: str, vote_type: str, feedback_text: str = None, user_id: str = None):
        """
        Records user feedback for a signal.
        """
        data = {
            "signal_id": signal_id,
            "vote_type": vote_type,
            "feedback_text": feedback_text,
            "user_id": user_id
        }
        try:
            return self.get_client().table("user_feedback").insert(data).execute()
        except Exception as e:
            print(f"FAILED TO SAVE FEEDBACK: {e}")

    def upsert_project_context(self, project_name: str, source_type: str, content_hash: str, dependencies: dict, tech_tags: list):
        """
        Stores the parsed project context (dependencies).
        """
        data = {
            "project_name": project_name,
            "source_type": source_type,
            "content_hash": content_hash,
            "dependencies": dependencies,
            "tech_tags": tech_tags,
            "last_updated": datetime.utcnow().isoformat()
        }
        # Assuming uniqueness on (project_name, source_type) via database constraint
        try:
            return self.get_client().table("project_context").upsert(data, on_conflict="project_name, source_type").execute()
        except Exception as e:
            print(f"FAILED TO UPSERT CONTEXT: {e}")

    def insert_conversation(self, conversation_id: str, role: str, content: str, intent: str = None, metadata: dict = None):
        """
        Saves a single chat message (user or assistant) to the conversations table.
        """
        data = {
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "intent": intent,
            "metadata": metadata or {}
        }
        try:
            return self.get_client().table("conversations").insert(data).execute()
        except Exception as e:
            print(f"FAILED TO SAVE CONVERSATION: {e}")

    def get_conversations(self, conversation_id: str, limit: int = 50):
        """
        Retrieves chat history for a given conversation.
        """
        try:
            result = self.get_client().table("conversations").select("*").eq(
                "conversation_id", conversation_id
            ).order("created_at", desc=False).limit(limit).execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"FAILED TO GET CONVERSATIONS: {e}")
            return []

    def query_signals(self, source: str = None, limit: int = 20):
        """
        Query raw_signals with optional source filter. Used by dashboard.
        """
        try:
            query = self.get_client().table("raw_signals").select("*").order("created_at", desc=True).limit(limit)
            if source:
                query = query.eq("source", source)
            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"FAILED TO QUERY SIGNALS: {e}")
            return []

    def query_intelligence(self, agent_name: str = None, limit: int = 20):
        """
        Query processed_intelligence with optional agent filter.
        """
        try:
            query = self.get_client().table("processed_intelligence").select("*").order("created_at", desc=True).limit(limit)
            if agent_name:
                query = query.eq("agent_name", agent_name)
            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"FAILED TO QUERY INTELLIGENCE: {e}")
            return []

# Global instance accessor
db = SupabaseManager()
