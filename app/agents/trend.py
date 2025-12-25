from typing import List, Dict, Any
from app.inference.client import BytezClient
from app.inference.selector import ModelSelector
from app.models.signal import Signal
from app.models.intelligence import TrendOutput
from app.core.logger import logger
from datetime import datetime
import json

class TrendDetectionAgent:
    """
    Analyzes a BATCH of signals to detect trends.
    Does not inherit from BaseAgent because it processes multiple signals.
    """
    def __init__(self, client: BytezClient):
        self.client = client

    @property
    def name(self) -> str:
        return "trend_detection"

    @property
    def model_id(self) -> str:
        return ModelSelector.get_model_for_task(self.name)

    async def analyze_batch(self, signals: List[Signal]) -> List[Dict[str, Any]]:
        if not signals:
            return []

        # Simple batching strategy: Concatenate titles/summaries
        # For large batches, we would need Map-Reduce or iterative refinement.
        # Here we assume a manageable daily batch or slice.
        
        combined_text = "\n".join([f"- {s.title} (ID: {s.external_id})" for s in signals[:20]]) # Limit to top 20 for context window
        
        prompt = f"""
        Identify top 3 emerging trends from these developer signals.
        Return raw JSON only. 
        Format: [
            {{
                "trend_name": "...", 
                "related_signals": ["id1", "id2"], 
                "growth_rate": "High/Stable"
            }}
        ]
        
        Signals:
        {combined_text}
        """

        try:
            response = await self.client.run_inference(
                model_id=self.model_id, 
                input_text=prompt
            )
            content = response['choices'][0]['message']['content']
            content = content.replace("```json", "").replace("```", "").strip()
            data = json.loads(content)
            
            results = []
            for item in data:
                # Validate against model
                output = TrendOutput(
                    trend_name=item.get("trend_name", "Unknown"),
                    related_signals=item.get("related_signals", []),
                    growth_rate=item.get("growth_rate", "Stable"),
                    agent_name=self.name,
                    model_used=self.model_id,
                    timestamp=datetime.utcnow().isoformat()
                )
                results.append(output.model_dump())
            return results

        except Exception as e:
            logger.error(f"Trend Agent Failed: {e}")
            return []
