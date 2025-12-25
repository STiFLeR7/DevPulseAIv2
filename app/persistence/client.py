import os
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

# Global instance accessor
db = SupabaseManager()
