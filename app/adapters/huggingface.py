import os
import httpx
from typing import List
from app.models.signal import Signal
from app.core.logger import logger

class HuggingFaceAdapter:
    BASE_URL = "https://huggingface.co/api"

    def __init__(self):
        self.token = os.environ.get("HUGGINGFACE_TOKEN")
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

    async def fetch_new_models(self) -> List[Signal]:
        """
        Fetches trending/new models from HF.
        """
        url = f"{self.BASE_URL}/models?sort=likes&direction=-1&limit=10"
        
        signals = []
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                
                for item in data:
                    signal = Signal(
                        source="huggingface",
                        external_id=item["modelId"],
                        title=f"HF Model: {item['modelId']}",
                        content=f"Tags: {item.get('tags', [])}\nDownloads: {item.get('downloads', 0)}\nLikes: {item.get('likes', 0)}",
                        url=f"https://huggingface.co/{item['modelId']}",
                        metadata=item
                    )
                    signals.append(signal)
        except Exception as e:
            logger.error(f"HF Adapter Error: {e}")
        
        return signals
