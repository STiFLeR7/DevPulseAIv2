import os
import asyncio
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from app.core.logger import logger

# Try import, but don't crash if missing during dev until installed
try:
    from bytez import Bytez
except ImportError:
    Bytez = None
    logger.warning("bytez SDK not found. Install with `pip install bytez`")

class BytezClient:
    """
    Client for interacting with Bytez.com inference API via official SDK.
    """
    def __init__(self):
        self.api_key = os.environ.get("BYTEZ_API_KEY")
        if not self.api_key:
            logger.warning("BYTEZ_API_KEY is not set. Inference will fail.")
        
        if Bytez and self.api_key:
            self.client = Bytez(self.api_key)
        else:
            self.client = None
            logger.warning("Bytez Client disabled (Missing Key or SDK)")
            
        self.executor = ThreadPoolExecutor(max_workers=5)

    async def run_inference(self, model_id: str, input_text: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes a prompt against a specified model on Bytez using the SDK.
        Returns a dictionary mimicking the OpenAI structure for compatibility with Agents.
        """
        if not self.client:
             # Fallback or Error
             raise RuntimeError("Bytez client not initialized.")

        def _call_sync():
            # Based on tests/test_bytez.py
            model = self.client.model(model_id)
            # Assuming .run() handles the generation
            return model.run(input_text)

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(self.executor, _call_sync)
            
            # Extract output based on test script logic
            output_content = ""
            if hasattr(result, 'output'):
                output_content = result.output
            elif hasattr(result, 'data'):
                output_content = result.data
            elif isinstance(result, dict):
                output_content = result.get('output') or result.get('data') or str(result)
            else:
                output_content = str(result)
            
            # Format to match what Agents expect (OpenAI style)
            return {
                "choices": [
                    {
                        "message": {
                            "content": output_content
                        }
                    }
                ]
            }
            
        except Exception as e:
            logger.error(f"Bytez Inference Failed for {model_id}: {e}")
            raise e
