import os
from google import genai
from typing import Dict, Any, Optional
from app.core.logger import logger

class GeminiClient:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not set. Inference will fail.")
            self.client = None
        else:
            self.client = genai.Client(api_key=self.api_key)
            self.model_name = "gemini-2.0-flash"

    async def run_inference(self, system_instruction: str = "You are a helpful assistant.", user_input: str = None, model_id: str = None, input_text: str = None, **kwargs) -> Dict[str, Any]:
        if not self.client:
            raise RuntimeError("Gemini Client not initialized.")
        
        # Normalize input (BaseAgent uses input_text, verify script uses user_input)
        prompt = user_input or input_text
        if not prompt:
            raise ValueError("No input provided (user_input or input_text required)")

        try:
            full_prompt = f"System: {system_instruction}\nUser: {prompt}"
            
            response = self.client.models.generate_content(
                model=self.model_name, contents=full_prompt
            )
            
            # Format to match OpenAI style for compatibility
            return {
                "choices": [
                    {
                        "message": {
                            "content": response.text
                        }
                    }
                ]
            }
        except Exception as e:
            logger.error(f"Gemini Inference Failed: {e}")
            raise e
