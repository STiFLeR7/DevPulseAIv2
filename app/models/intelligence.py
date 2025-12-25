from pydantic import BaseModel, Field
from typing import List, Optional

class AgentOutput(BaseModel):
    agent_name: str
    model_used: str
    timestamp: str

class SummarizationOutput(AgentOutput):
    summary_text: str = Field(..., description="Concise summary of the signal")
    key_points: List[str] = Field(default_factory=list, description="Bulleted key takeaways")

class RelevanceOutput(AgentOutput):
    score: float = Field(..., description="Relevance score between 0 and 100")
    reasoning: str = Field(..., description="Why this content is relevant or not")

class RiskOutput(AgentOutput):
    risk_level: str = Field(..., description="LOW, MEDIUM, HIGH")
    security_concerns: List[str] = Field(default_factory=list)
    breaking_changes: bool = Field(False)

class TrendOutput(AgentOutput):
    trend_name: str
    related_signals: List[str] # List of External IDs
    growth_rate: str # e.g. "High", "Stable"
