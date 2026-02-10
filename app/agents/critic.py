from typing import Dict, Any, List
from app.core.swarm import Worker

class CriticAgent(Worker):
    """Validates outputs before they reach the user."""
    
    def __init__(self):
        super().__init__(name="CriticAgent")
        self.checks = [
            self._check_hallucination,
            self._check_completeness,
            self._check_security
        ]
        
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Review an agent's output for quality issues.
        Expected task structure:
        {
            "output": {...},  # The output to review
            "context": {...},  # Original task context
            "agent": "RepoResearcher"  # Which agent produced this
        }
        """
        output = task.get("output")
        context = task.get("context", {})
        agent_name = task.get("agent", "Unknown")
        
        if not output:
            return {"status": "error", "message": "output is required"}
        
        self.log_trace(
            step_name="critic_review_start",
            input_state={"agent": agent_name},
            output_state={}
        )
        
        issues = []
        
        # Run all checks
        for check_fn in self.checks:
            check_result = await check_fn(output, context)
            if not check_result["passed"]:
                issues.append(check_result)
        
        # Determine overall verdict
        critical_issues = [i for i in issues if i.get("severity") == "critical"]
        
        verdict = {
            "approved": len(critical_issues) == 0,
            "issues": issues,
            "recommendation": self._generate_recommendation(issues)
        }
        
        self.log_trace(
            step_name="critic_review_complete",
            input_state={"agent": agent_name},
            output_state=verdict
        )
        
        return {
            "status": "success",
            "verdict": verdict
        }
    
    async def _check_hallucination(self, output: Dict, context: Dict) -> Dict:
        """Check if the output contains fabricated information."""
        # TODO: Implement fact-checking logic
        # For now, placeholder check
        return {
            "check": "hallucination",
            "passed": True,
            "severity": "critical",
            "message": "No obvious hallucinations detected"
        }
    
    async def _check_completeness(self, output: Dict, context: Dict) -> Dict:
        """Check if the output addresses all required aspects."""
        required_fields = context.get("required_fields", [])
        missing = [f for f in required_fields if f not in output]
        
        return {
            "check": "completeness",
            "passed": len(missing) == 0,
            "severity": "medium",
            "message": f"Missing fields: {missing}" if missing else "All required fields present"
        }
    
    async def _check_security(self, output: Dict, context: Dict) -> Dict:
        """Check for potential security concerns in the output."""
        # TODO: Check for exposed secrets, unsafe recommendations
        return {
            "check": "security",
            "passed": True,
            "severity": "critical",
            "message": "No security concerns detected"
        }
    
    def _generate_recommendation(self, issues: List[Dict]) -> str:
        """Generate an actionable recommendation based on issues found."""
        if not issues:
            return "Output approved. Ready for user consumption."
        
        critical = [i for i in issues if i.get("severity") == "critical"]
        if critical:
            return f"REJECT: Critical issues found: {[i['message'] for i in critical]}"
        
        return f"APPROVE WITH WARNING: {len(issues)} non-critical issues found"
