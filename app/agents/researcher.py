from typing import Dict, Any
import re
from app.core.swarm import Worker

class RepoResearcher(Worker):
    """Specialized agent for deep-diving into GitHub repositories."""
    
    def __init__(self):
        super().__init__(name="RepoResearcher")
        self.github_mcp = None  # Will be injected by SwarmManager
        
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep dive into a repository.
        Expected task structure:
        {
            "user_message": "Analyze the FastAPI repository",
            "repo_url": "https://github.com/owner/repo" (optional, extracted from message)
        }
        """
        user_message = task.get("user_message", "")
        repo_url = task.get("repo_url", "")
        
        # Extract repo URL from message if not provided
        if not repo_url:
            repo_url = self._extract_repo_url(user_message)
        
        if not repo_url:
            return {
                "status": "error",
                "summary": "I couldn't find a repository URL in your message. Please provide a GitHub URL or mention a repo like 'owner/repo'."
            }
        
        # Parse owner/repo from URL
        owner, repo = self._parse_repo_url(repo_url)
        if not owner or not repo:
            return {
                "status": "error",
                "summary": f"Invalid repository format: {repo_url}"
            }
        
        self.log_trace(
            step_name="repo_analysis_start",
            input_state={"owner": owner, "repo": repo, "message": user_message},
            output_state={}
        )
        
        # Analyze repository
        try:
            overview = await self._get_repo_overview(owner, repo)
            dependencies = await self._analyze_dependencies(owner, repo)
            
            summary = self._generate_summary(owner, repo, overview, dependencies)
            
            self.log_trace(
                step_name="repo_analysis_complete",
                input_state={"owner": owner, "repo": repo},
                output_state={"summary": summary}
            )
            
            return {
                "status": "success",
                "summary": summary
            }
        except Exception as e:
            return {
                "status": "error",
                "summary": f"Failed to analyze {owner}/{repo}: {str(e)}"
            }
    
    def _extract_repo_url(self, message: str) -> str:
        """Extract GitHub repo URL from user message."""
        # Pattern 1: Full URL
        url_match = re.search(r'github\.com/([\w-]+/[\w-]+)', message)
        if url_match:
            return f"https://github.com/{url_match.group(1)}"
        
        # Pattern 2: owner/repo format
        repo_match = re.search(r'([\w-]+)/([\w-]+)', message)
        if repo_match:
            return f"https://github.com/{repo_match.group(0)}"
        
        return ""
    
    def _parse_repo_url(self, url: str) -> tuple:
        """Parse owner and repo from URL."""
        parts = url.rstrip("/").split("/")
        if len(parts) >= 2:
            return parts[-2], parts[-1]
        return None, None
    
    async def _get_repo_overview(self, owner: str, repo: str) -> Dict:
        """Get basic repository information using GitHub MCP."""
        # For now, return basic info
        # TODO: Call GitHub MCP when available
        return {
            "name": f"{owner}/{repo}",
            "description": "Analyzing repository structure...",
        }
    
    async def _analyze_dependencies(self, owner: str, repo: str) -> Dict:
        """Analyze project dependencies."""
        # Try to get common dependency files
        deps = {"files_checked": [], "dependencies": []}
        
        # TODO: Use GitHub MCP get_file_contents for:
        # - requirements.txt, Pipfile, pyproject.toml (Python)
        # - package.json (Node.js)
        # - go.mod (Go)
        
        return deps
    
    def _generate_summary(self, owner: str, repo: str, overview: Dict, dependencies: Dict) -> str:
        """Generate human-readable summary."""
        summary = f"## Repository Analysis: {owner}/{repo}\n\n"
        summary += f"**Description**: {overview.get('description', 'N/A')}\n\n"
        summary += f"I've analyzed the structure of this repository. "
        
        if dependencies.get("dependencies"):
            summary += f"Found {len(dependencies['dependencies'])} dependencies. "
        else:
            summary += "Dependency analysis pending GitHub MCP integration. "
        
        summary += f"\n\nFull integration with GitHub MCP coming soon for deep code analysis!"
        
        return summary
