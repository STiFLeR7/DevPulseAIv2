import os
import time
from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

load_dotenv()

class VectorStore:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorStore, cls).__new__(cls)
            cls._instance._init_client()
        return cls._instance

    def _init_client(self):
        api_key = os.environ.get("PINECONE_API_KEY")
        self.index_name = os.environ.get("PINECONE_INDEX_NAME", "devpulse-v3-memory")
        
        if not api_key:
            print("WARNING: PINECONE_API_KEY not set. Vector memory will be disabled.")
            self.client = None
            self.index = None
            return

        self.client = Pinecone(api_key=api_key)
        
        # Check if index exists, if not create it (Serverless)
        existing_indexes = [i.name for i in self.client.list_indexes()]
        if self.index_name not in existing_indexes:
            print(f"Creating Pinecone index: {self.index_name}")
            try:
                self.client.create_index(
                    name=self.index_name,
                    dimension=1536, # Standard for text-embedding-ada-002 or similar
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                # Wait for index to be ready
                while not self.client.describe_index(self.index_name).status['ready']:
                    time.sleep(1)
            except Exception as e:
                print(f"Failed to create Pinecone index: {e}")
                
        self.index = self.client.Index(self.index_name)

    def upsert_entity(self, entity_id: str, vector: List[float], metadata: Dict[str, Any]):
        """
        Stores an entity (paper, repo, author) in the vector store.
        """
        if not self.index:
            return None
            
        try:
            self.index.upsert(vectors=[(entity_id, vector, metadata)])
            return True
        except Exception as e:
            print(f"Vector upsert failed: {e}")
            return False

    def query_similar(self, vector: List[float], top_k: int = 5, filter_criteria: Dict = None):
        """
        Finds semantically similar entities.
        """
        if not self.index:
            return []
            
        try:
            results = self.index.query(
                vector=vector,
                top_k=top_k,
                include_metadata=True,
                filter=filter_criteria
            )
            return results.matches
        except Exception as e:
            print(f"Vector query failed: {e}")
            return []

    def delete_entity(self, entity_id: str):
        if not self.index:
            return
        
        try:
            self.index.delete(ids=[entity_id])
        except Exception as e:
            print(f"Vector delete failed: {e}")

# Global Accessor
vector_store = VectorStore()
