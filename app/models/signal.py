from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime
import hashlib
import json

class Signal(BaseModel):
    """
    Normalized data structure for any ingested signal.
    """
    source: str = Field(..., description="Source of the signal (github, huggingface, medium)")
    external_id: str = Field(..., description="Unique ID from the source")
    title: str = Field(..., description="Title or headline")
    content: str = Field(..., description="Main content body for analysis")
    url: str = Field(..., description="URL to the original resource")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extra raw data")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def generate_hash(self) -> str:
        """
        Generates a deterministic hash of the signal content for deduplication.
        """
        payload = {
            "source": self.source,
            "external_id": self.external_id,
            "content": self.content
        }
        # sort_keys=True ensures deterministic JSON string
        serialized = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

class IngestionResult(BaseModel):
    source: str
    signals_fetched: int
    signals_new: int
    errors: int
