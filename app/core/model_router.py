"""
Cost-Aware Model Routing — SOW §7

Tiered model selection: lightweight for ingestion, strong for synthesis.

Tiers:
  FAST   → gpt-4.1-mini    (ingestion, cleanup, classification)
  MID    → gpt-4.1-mini    (worker reasoning, default)
  STRONG → gpt-4.1         (synthesis, final output)

Override via environment variables: MODEL_FAST, MODEL_MID, MODEL_STRONG
"""

import os
from typing import Dict, Optional
from app.core.logger import logger


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Model Tier Definitions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Default models per tier (OpenAI pricing as of Feb 2026)
DEFAULT_MODELS = {
    "fast": "gpt-4.1-mini",       # ~$0.40/M input  — ingestion, simple tasks
    "mid": "gpt-4.1-mini",        # ~$0.40/M input  — worker reasoning
    "strong": "gpt-4.1",          # ~$2.00/M input  — synthesis, final output
}

# Cost per million tokens (approximate, USD)
COST_TABLE = {
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
    "gpt-4.1": {"input": 2.00, "output": 8.00},
    "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
    "gemini-2.5-pro": {"input": 1.25, "output": 10.00},
}


class ModelRouter:
    """
    Tier-based model selection with cost estimation.

    Usage:
        router = ModelRouter()
        model = router.get_model("fast")          # → "gpt-4.1-mini"
        model = router.get_model("strong")         # → "gpt-4.1"
        cost = router.estimate_cost("gpt-4.1", 1000, 500)  # → $0.006
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        """Load model config from env vars or defaults."""
        self.models = {
            "fast": os.environ.get("MODEL_FAST", DEFAULT_MODELS["fast"]),
            "mid": os.environ.get("MODEL_MID", DEFAULT_MODELS["mid"]),
            "strong": os.environ.get("MODEL_STRONG", DEFAULT_MODELS["strong"]),
        }
        self._total_cost_usd = 0.0

        logger.info(
            f"ModelRouter initialized: fast={self.models['fast']}, "
            f"mid={self.models['mid']}, strong={self.models['strong']}"
        )

    def get_model(self, tier: str = "mid") -> str:
        """
        Get the model ID for a given tier.

        Args:
            tier: "fast", "mid", or "strong"

        Returns:
            Model identifier string
        """
        return self.models.get(tier, self.models["mid"])

    def estimate_cost(self, model: str, input_tokens: int,
                      output_tokens: int = 0) -> float:
        """
        Estimate the cost in USD for a model call.

        Returns cost in USD (float).
        """
        costs = COST_TABLE.get(model, {"input": 1.0, "output": 4.0})
        input_cost = (input_tokens / 1_000_000) * costs["input"]
        output_cost = (output_tokens / 1_000_000) * costs["output"]
        return round(input_cost + output_cost, 6)

    def log_usage(self, model: str, input_tokens: int,
                  output_tokens: int = 0, context: str = ""):
        """
        Log a model usage event and accumulate cost.
        """
        cost = self.estimate_cost(model, input_tokens, output_tokens)
        self._total_cost_usd += cost
        logger.info(
            f"ModelRouter: {model} | {input_tokens}→{output_tokens} tokens | "
            f"${cost:.6f} | total=${self._total_cost_usd:.4f} | {context}"
        )

    @property
    def total_cost(self) -> float:
        """Get total accumulated cost in USD."""
        return round(self._total_cost_usd, 4)

    def status(self) -> Dict:
        """Get router status."""
        return {
            "models": self.models,
            "total_cost_usd": self.total_cost,
            "cost_table": COST_TABLE,
        }


# Singleton accessor
router = ModelRouter()
