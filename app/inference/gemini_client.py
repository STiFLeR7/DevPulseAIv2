import os
import google.generativeai as genai
from typing import Dict, Any, Optional
from app.core.logger import logger

class GeminiClient:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not set. Inference will fail.")
            self.model = None
        else:
            genai.configure(api_key=self.api_key)
            # 'gemini-1.5-flash' not found, using 'gemini-flash-latest'
            self.model = genai.GenerativeModel('gemini-flash-latest')

    async def run_inference(self, system_instruction: str = "You are a helpful assistant.", user_input: str = None, model_id: str = None, input_text: str = None, **kwargs) -> Dict[str, Any]:
        if not self.model:
            raise RuntimeError("Gemini Client not initialized.")
        
        # Normalize input (BaseAgent uses input_text, verify script uses user_input)
        prompt = user_input or input_text
        if not prompt:
            raise ValueError("No input provided (user_input or input_text required)")

        try:
            # Gemini 1.5 Flash doesn't support 'system_instruction' param in strict OpenAI sense in older SDKs,
            # but usually we prepend it or use the system_instruction arg if available.
            # Best practice for simple usage: Combined prompt.
            full_prompt = f"System: {system_instruction}\nUser: {prompt}"
            
            response = self.model.generate_content(full_prompt)
            
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
