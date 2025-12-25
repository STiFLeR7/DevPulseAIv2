from abc import ABC, abstractmethod
from typing import Any, Dict
from app.models.signal import Signal
from app.inference.client import BytezClient
from app.inference.selector import ModelSelector
from app.core.logger import logger
from datetime import datetime

class BaseAgent(ABC):
    def __init__(self, client: BytezClient):
        self.client = client

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    def model_id(self) -> str:
        return ModelSelector.get_model_for_task(self.name)

    async def process(self, signal: Signal) -> Dict[str, Any]:
        """
        Main entry point for processing a signal.
        Orchestrates prompt building, inference, and parsing.
        """
        logger.info(f"Agent {self.name} processing signal {signal.external_id}")
        
        prompt = self.build_prompt(signal)
        try:
            response = await self.client.run_inference(
                model_id=self.model_id, 
                input_text=prompt
            )
            parsed = self.parse_output(response, signal)
            parsed["timestamp"] = datetime.utcnow().isoformat()
            parsed["agent_name"] = self.name
            parsed["model_used"] = self.model_id
            return parsed
        except Exception as e:
            logger.error(f"Agent {self.name} failed: {e}")
            raise e

    @abstractmethod
    def build_prompt(self, signal: Signal) -> str:
        """Constructs the prompt for the LLM."""
        pass

    @abstractmethod
    def parse_output(self, llm_response: Dict[str, Any], signal: Signal) -> Dict[str, Any]:
        """Parses the raw LLM JSON response into a structured dict."""
        pass
