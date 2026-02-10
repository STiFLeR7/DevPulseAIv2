import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.memory.vector_store import VectorStore

class TestVectorStore(unittest.TestCase):
    
    @patch('app.memory.vector_store.Pinecone')
    @patch('os.environ.get')
    def test_init_client(self, mock_env, mock_pinecone):
        # Mock environment variables
        mock_env.return_value = "test-api-key"
        
        # Reset singleton for testing
        VectorStore._instance = None
        
        store = VectorStore()
        
        # Verify Pinecone client was initialized
        mock_pinecone.assert_called_with(api_key="test-api-key")
        
        # Verify index creation check (list_indexes called)
        store.client.list_indexes.assert_called()

    @patch('app.memory.vector_store.Pinecone')
    @patch('os.environ.get')
    def test_upsert_entity(self, mock_env, mock_pinecone):
        mock_env.return_value = "test-api-key"
        VectorStore._instance = None
        store = VectorStore()
        
        # Mock the index object
        mock_index = MagicMock()
        store.index = mock_index
        
        # Call upsert
        success = store.upsert_entity(
            entity_id="test-id",
            vector=[0.1, 0.2, 0.3],
            metadata={"type": "test"}
        )
        
        # Verify result and call
        self.assertTrue(success)
        mock_index.upsert.assert_called_with(
            vectors=[("test-id", [0.1, 0.2, 0.3], {"type": "test"})]
        )

if __name__ == "__main__":
    unittest.main()
