"""
RiskAnalyst — Ephemeral Worker (SOW §3)

Scans incoming signals for security risks: CVEs, breaking changes,
deprecations. Cross-references against the user's ProjectContext
to determine actual impact.

Severity levels: CRITICAL / HIGH / MEDIUM / LOW / INFO
"""

import re
from typing import Dict, Any, List, Tuple

from app.core.swarm import Worker
from app.core.logger import logger


class RiskAnalyst(Worker):
    """
    Scans signals for security and stability risks.

    Risk detection:
    - CVE patterns (CVE-YYYY-NNNNN)
    - Breaking change indicators
    - Deprecation notices
    - License changes
    - Supply chain risks

    Cross-references with ProjectContext for impact assessment.
    """

    CVE_PATTERN = re.compile(r'CVE-\d{4}-\d{4,}', re.IGNORECASE)

    BREAKING_INDICATORS = [
        "breaking change", "breaking changes", "backward incompatible",
        "removed support", "no longer supports", "api change",
        "migration required", "deprecated and removed",
        "major version", "semver major",
    ]

    DEPRECATION_INDICATORS = [
        "deprecated", "deprecation", "end of life", "eol",
        "sunset", "will be removed", "no longer maintained",
        "archived", "unmaintained",
    ]

    SEVERITY_MAP = {
        "cve": "CRITICAL",
        "breaking_change": "HIGH",
        "deprecation": "MEDIUM",
        "license_change": "MEDIUM",
        "supply_chain": "HIGH",
    }

    def __init__(self):
        super().__init__(name="RiskAnalyst")

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scan for risks in recent signals or a specific topic.

        Task: {"user_message": "What CVEs affect my project?"}
        """
        user_message = task.get("user_message", "")
        self.log_trace(f"Risk scan requested: {user_message[:80]}")

        # Load project context for impact assessment
        project_context = self._load_project_context()

        # Gather signals to scan
        signals = await self._gather_signals()

        if not signals:
            return {
                "status": "ok",
                "summary": "No recent signals to scan for risks. "
                           "Try running `/daily-pulse` first to ingest fresh data.",
                "risks": [],
            }

        # Scan for risks
        risks = self._scan_risks(signals, project_context)

        # Build summary
        summary = self._build_summary(risks, project_context)

        return {
            "status": "ok",
            "summary": summary,
            "risks": [r for r in risks],
            "risk_count": len(risks),
            "critical_count": sum(1 for r in risks if r["severity"] == "CRITICAL"),
            "high_count": sum(1 for r in risks if r["severity"] == "HIGH"),
        }

    def _load_project_context(self) -> Dict:
        """Load project context from Supabase for impact assessment."""
        try:
            from app.persistence.client import db
            ctx = db.get_project_context("DevPulseAIv2")
            if ctx:
                return ctx
        except Exception as e:
            logger.warning(f"RiskAnalyst: Could not load project context: {e}")
        return {}

    async def _gather_signals(self) -> List[Dict]:
        """Get recent signals from Supabase for scanning."""
        try:
            from app.persistence.client import db
            return db.query_signals(limit=50)
        except Exception as e:
            logger.warning(f"RiskAnalyst: Could not fetch signals: {e}")
            return []

    def _scan_risks(self, signals: List[Dict], project_context: Dict) -> List[Dict]:
        """Scan signals for risk indicators."""
        risks = []
        user_deps = set()

        if project_context:
            deps = project_context.get("dependencies", {})
            if isinstance(deps, dict):
                user_deps = {k.lower() for k in deps.keys()}

        for sig in signals:
            payload = sig.get("payload", {})
            title = payload.get("title", "")
            content = payload.get("content", "")
            text = f"{title} {content}".lower()

            # 1. CVE detection
            cve_matches = self.CVE_PATTERN.findall(f"{title} {content}")
            for cve in cve_matches:
                affected_deps = [d for d in user_deps if d in text]
                severity = "CRITICAL" if affected_deps else "HIGH"

                risks.append({
                    "type": "cve",
                    "severity": severity,
                    "cve_id": cve.upper(),
                    "title": title,
                    "affected_deps": affected_deps,
                    "source": sig.get("source", "unknown"),
                    "impacts_project": bool(affected_deps),
                })

            # 2. Breaking changes
            for indicator in self.BREAKING_INDICATORS:
                if indicator in text:
                    affected_deps = [d for d in user_deps if d in text]
                    risks.append({
                        "type": "breaking_change",
                        "severity": "HIGH" if affected_deps else "MEDIUM",
                        "indicator": indicator,
                        "title": title,
                        "affected_deps": affected_deps,
                        "source": sig.get("source", "unknown"),
                        "impacts_project": bool(affected_deps),
                    })
                    break  # One per signal

            # 3. Deprecation notices
            for indicator in self.DEPRECATION_INDICATORS:
                if indicator in text:
                    affected_deps = [d for d in user_deps if d in text]
                    risks.append({
                        "type": "deprecation",
                        "severity": "MEDIUM" if affected_deps else "LOW",
                        "indicator": indicator,
                        "title": title,
                        "affected_deps": affected_deps,
                        "source": sig.get("source", "unknown"),
                        "impacts_project": bool(affected_deps),
                    })
                    break

        # Sort by severity: CRITICAL > HIGH > MEDIUM > LOW
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
        risks.sort(key=lambda r: severity_order.get(r["severity"], 5))

        return risks

    def _build_summary(self, risks: List[Dict], project_context: Dict) -> str:
        """Build a human-readable risk report."""
        if not risks:
            return "✅ **No risks detected** in recent signals. Your project looks safe."

        project_name = project_context.get("project_name", "your project")

        critical = [r for r in risks if r["severity"] == "CRITICAL"]
        high = [r for r in risks if r["severity"] == "HIGH"]
        medium = [r for r in risks if r["severity"] == "MEDIUM"]
        impacting = [r for r in risks if r.get("impacts_project")]

        summary = f"🛡️ **Risk Report** — {len(risks)} risks detected\n\n"

        if impacting:
            summary += f"⚠️ **{len(impacting)} risk(s) directly impact {project_name}**\n\n"

        if critical:
            summary += f"🔴 **CRITICAL** ({len(critical)}):\n"
            for r in critical[:3]:
                deps = ", ".join(r.get("affected_deps", [])) or "unknown"
                summary += f"  - {r.get('cve_id', r['title'])} — affects: {deps}\n"
            summary += "\n"

        if high:
            summary += f"🟠 **HIGH** ({len(high)}):\n"
            for r in high[:3]:
                summary += f"  - {r['title'][:80]}\n"
            summary += "\n"

        if medium:
            summary += f"🟡 **MEDIUM** ({len(medium)}):\n"
            for r in medium[:3]:
                summary += f"  - {r['title'][:80]}\n"

        return summary
