"""
DependencyImpactAnalyzer — Ephemeral Worker (SOW §3)

Given a package update, CVE, or breaking change, traces impact
through the project's dependency chain to identify affected components.

Uses ProjectContext from Codebase-Aware Intelligence (SOW §5).
"""

from typing import Dict, Any, List

from app.core.swarm import Worker
from app.core.logger import logger


class DependencyImpactAnalyzer(Worker):
    """
    Traces the impact of a dependency change through the project.

    Given:  "httpx has a new CVE"
    Returns: which parts of the project use httpx, risk level,
             and recommended actions.
    """

    def __init__(self):
        super().__init__(name="DependencyImpactAnalyzer")

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze dependency impact.

        Task: {"user_message": "What's the impact of updating httpx?"}
        """
        user_message = task.get("user_message", "")
        target_dep = self._extract_dependency(user_message)

        if not target_dep:
            return {
                "status": "error",
                "summary": "I couldn't identify a dependency to analyze. "
                           "Try: 'What's the impact of updating FastAPI?'"
            }

        self.log_trace(f"Analyzing dependency impact: {target_dep}")

        # Load project context
        project_context = self._load_project_context()

        if not project_context:
            return {
                "status": "error",
                "summary": "No project context found. Run `POST /api/context` first "
                           "to scan your project dependencies.",
            }

        # Analyze impact
        impact = self._analyze_impact(target_dep, project_context)

        return {
            "status": "ok",
            "summary": impact["summary"],
            "dependency": target_dep,
            "is_direct_dep": impact["is_direct_dep"],
            "is_dev_dep": impact["is_dev_dep"],
            "current_version": impact["current_version"],
            "risk_level": impact["risk_level"],
            "affected_areas": impact["affected_areas"],
            "recommendations": impact["recommendations"],
        }

    def _extract_dependency(self, message: str) -> str:
        """Extract the dependency name from user message."""
        # Common patterns: "impact of updating X", "what about X update"
        message_lower = message.lower()

        for prefix in ["impact of updating", "impact of", "updating",
                       "what about", "what if", "upgrade"]:
            if prefix in message_lower:
                after = message_lower.split(prefix)[-1].strip().strip("?.")
                words = after.split()
                if words:
                    return words[0].strip()

        # Fallback: find known package names in the message
        try:
            from app.memory.graph import KNOWN_LIBRARIES
            for lib in KNOWN_LIBRARIES:
                if lib in message_lower:
                    return lib
        except ImportError:
            pass

        return ""

    def _load_project_context(self) -> Dict:
        """Load project context from Supabase."""
        try:
            from app.persistence.client import db
            return db.get_project_context("DevPulseAIv2")
        except Exception:
            return {}

    def _analyze_impact(self, target_dep: str, context: Dict) -> Dict:
        """Analyze the impact of updating/removing a dependency."""
        direct_deps = context.get("dependencies", {})
        dev_deps = context.get("dev_dependencies", {})
        frameworks = context.get("frameworks", [])
        tech_tags = context.get("tech_tags", [])

        target_lower = target_dep.lower()

        is_direct = target_lower in {k.lower() for k in direct_deps}
        is_dev = target_lower in {k.lower() for k in dev_deps}
        current_version = direct_deps.get(target_dep, dev_deps.get(target_dep, "unknown"))

        # Determine affected areas
        affected_areas = []
        if target_lower in {"fastapi", "flask", "django", "express"}:
            affected_areas.append("API/Web Layer")
        if target_lower in {"openai", "anthropic", "gemini", "transformers", "langchain"}:
            affected_areas.append("AI/LLM Pipeline")
        if target_lower in {"supabase", "redis", "postgres", "mongodb", "prisma"}:
            affected_areas.append("Data/Persistence Layer")
        if target_lower in {"pinecone", "chromadb", "weaviate"}:
            affected_areas.append("Vector Store / RAG")
        if target_lower in {"httpx", "aiohttp", "requests"}:
            affected_areas.append("HTTP/Network Layer")
        if target_lower in {"pytest", "mypy", "ruff", "eslint"}:
            affected_areas.append("Dev Tooling")
        if target_lower in {"streamlit", "gradio", "react", "next"}:
            affected_areas.append("UI Layer")
        if not affected_areas:
            affected_areas.append("Unknown — manual review needed")

        # Determine risk level
        if not is_direct and not is_dev:
            risk_level = "NONE"
            recommendations = [
                f"'{target_dep}' is not a dependency of this project.",
                "No action needed unless it's a transitive dependency.",
            ]
        elif target_lower in (f.lower() for f in frameworks):
            risk_level = "HIGH"
            recommendations = [
                f"'{target_dep}' is a core framework — update with caution.",
                "Check the changelog for breaking changes before upgrading.",
                "Run full test suite after updating.",
                "Consider pinning to a specific minor version.",
            ]
        elif is_direct:
            risk_level = "MEDIUM"
            recommendations = [
                f"'{target_dep}' is a direct dependency (version: {current_version}).",
                "Review the changelog and check for breaking API changes.",
                "Test the critical paths that use this dependency.",
            ]
        else:
            risk_level = "LOW"
            recommendations = [
                f"'{target_dep}' is a dev dependency — lower production risk.",
                "Update when convenient, test dev workflows.",
            ]

        # Build summary
        if risk_level == "NONE":
            summary = (
                f"ℹ️ **'{target_dep}'** is not a dependency of this project. "
                "No impact expected."
            )
        else:
            risk_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(risk_level, "⚪")
            dep_type = "direct" if is_direct else "dev"

            summary = (
                f"{risk_emoji} **Dependency Impact: {target_dep}**\n\n"
                f"- **Status**: {dep_type} dependency (v{current_version})\n"
                f"- **Risk Level**: {risk_level}\n"
                f"- **Affected Areas**: {', '.join(affected_areas)}\n\n"
                f"**Recommendations**:\n"
                + "\n".join(f"  {i+1}. {r}" for i, r in enumerate(recommendations))
            )

        return {
            "summary": summary,
            "is_direct_dep": is_direct,
            "is_dev_dep": is_dev,
            "current_version": current_version,
            "risk_level": risk_level,
            "affected_areas": affected_areas,
            "recommendations": recommendations,
        }
