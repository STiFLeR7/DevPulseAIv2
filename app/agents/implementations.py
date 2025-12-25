import json
from typing import Dict, Any
from app.agents.base import BaseAgent
from app.models.signal import Signal
from app.models.intelligence import SummarizationOutput, RelevanceOutput, RiskOutput

class SummarizationAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "summarization"

    def build_prompt(self, signal: Signal) -> str:
        return f"""
        You are a technical summarization expert. 
        Analyze the following developer signal and provide a concise summary and key points.
        Return raw JSON only, no markdown. Format: {{"summary_text": "...", "key_points": ["...", "..."]}}
        
        Title: {signal.title}
        Content: {signal.content}
        """

    def parse_output(self, llm_response: Dict[str, Any], signal: Signal) -> Dict[str, Any]:
        content = llm_response['choices'][0]['message']['content']
        try:
            # Clean possible markdown formatting
            content = content.replace("```json", "").replace("```", "").strip()
            data = json.loads(content)
            return SummarizationOutput(
                summary_text=data.get("summary_text", ""),
                key_points=data.get("key_points", []),
                agent_name=self.name,
                model_used=self.model_id,
                timestamp="" # Filled by base
            ).model_dump()
        except Exception:
            # Fallback for parsing failures - critical for resilience
            return SummarizationOutput(
                summary_text="Failed to parse summary.",
                agent_name=self.name,
                model_used=self.model_id,
                timestamp=""
            ).model_dump()

class RelevanceAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "relevance"

    def build_prompt(self, signal: Signal) -> str:
        return f"""
        Rate the relevance of this signal for a Senior AI Platform Architect.
        Score from 0-100.
        Return raw JSON only. Format: {{"score": 85, "reasoning": "..."}}
        
        Title: {signal.title}
        Content: {signal.content}
        """

    def parse_output(self, llm_response: Dict[str, Any], signal: Signal) -> Dict[str, Any]:
        content = llm_response['choices'][0]['message']['content']
        try:
            content = content.replace("```json", "").replace("```", "").strip()
            data = json.loads(content)
            return RelevanceOutput(
                score=float(data.get("score", 0)),
                reasoning=data.get("reasoning", "No reasoning provided"),
                agent_name=self.name,
                model_used=self.model_id,
                timestamp=""
            ).model_dump()
        except:
             return RelevanceOutput(
                score=0,
                reasoning="Parsing Failed",
                agent_name=self.name,
                model_used=self.model_id,
                timestamp=""
            ).model_dump()

class RiskAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "risk_analysis"

    def build_prompt(self, signal: Signal) -> str:
        return f"""
        Analyze for security risks or breaking changes.
        Return raw JSON only. Format: {{"risk_level": "LOW|MEDIUM|HIGH", "security_concerns": [], "breaking_changes": boolean}}
        
        Title: {signal.title}
        Content: {signal.content}
        """

    def parse_output(self, llm_response: Dict[str, Any], signal: Signal) -> Dict[str, Any]:
        content = llm_response['choices'][0]['message']['content']
        try:
            content = content.replace("```json", "").replace("```", "").strip()
            data = json.loads(content)
            return RiskOutput(
                risk_level=data.get("risk_level", "LOW"),
                security_concerns=data.get("security_concerns", []),
                breaking_changes=data.get("breaking_changes", False),
                agent_name=self.name,
                model_used=self.model_id,
                timestamp=""
            ).model_dump()
        except:
            return RiskOutput(
                risk_level="UNKNOWN",
                agent_name=self.name,
                model_used=self.model_id,
                timestamp=""
            ).model_dump()
