"""
RepoResearcher — GitHub Repository Analysis Agent

Uses the real GitHub REST API to fetch repo metadata, README, languages,
and recent commits. Stores results as raw_signals in Supabase.
"""

import os
import re
import hashlib
import httpx
from typing import Dict, Any

from app.core.swarm import Worker
from app.persistence.client import db


class RepoResearcher(Worker):
    """Specialized agent for deep-diving into GitHub repositories."""

    GITHUB_API = "https://api.github.com"

    def __init__(self):
        super().__init__(name="RepoResearcher")
        self.token = os.environ.get("GITHUB_TOKEN")
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep dive into a repository.
        Expected task: {"user_message": "Analyze the FastAPI repository"}
        """
        user_message = task.get("user_message", "")
        repo_url = task.get("repo_url", "")

        if not repo_url:
            repo_url = self._extract_repo_url(user_message)

        if not repo_url:
            return {
                "status": "error",
                "summary": "I couldn't find a repository URL in your message. "
                           "Please provide a GitHub URL or mention a repo like 'owner/repo'."
            }

        owner, repo = self._parse_repo_url(repo_url)
        if not owner or not repo:
            return {"status": "error", "summary": f"Invalid repository format: {repo_url}"}

        self.log_trace(
            step_name="repo_analysis_start",
            input_state={"owner": owner, "repo": repo, "message": user_message},
            output_state={}
        )

        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                # Fetch repo metadata, README, languages, recent commits in parallel
                repo_resp = await client.get(
                    f"{self.GITHUB_API}/repos/{owner}/{repo}", headers=self.headers
                )
                readme_resp = await client.get(
                    f"{self.GITHUB_API}/repos/{owner}/{repo}/readme", headers=self.headers
                )
                langs_resp = await client.get(
                    f"{self.GITHUB_API}/repos/{owner}/{repo}/languages", headers=self.headers
                )
                commits_resp = await client.get(
                    f"{self.GITHUB_API}/repos/{owner}/{repo}/commits?per_page=5", headers=self.headers
                )

            # Parse responses
            if repo_resp.status_code != 200:
                return {"status": "error", "summary": f"GitHub API error ({repo_resp.status_code}): {repo_resp.text[:200]}"}

            repo_data = repo_resp.json()
            languages = langs_resp.json() if langs_resp.status_code == 200 else {}
            readme_data = readme_resp.json() if readme_resp.status_code == 200 else {}
            commits_data = commits_resp.json() if commits_resp.status_code == 200 else []

            # Decode README (base64)
            readme_content = ""
            if readme_data.get("content"):
                import base64
                try:
                    readme_content = base64.b64decode(readme_data["content"]).decode("utf-8", errors="replace")[:2000]
                except Exception:
                    readme_content = "(Could not decode README)"

            # Build summary
            summary = self._generate_summary(owner, repo, repo_data, languages, commits_data, readme_content)

            # Persist to Supabase as raw_signal + processed_intelligence
            signal_payload = {
                "name": repo_data.get("full_name"),
                "description": repo_data.get("description"),
                "stars": repo_data.get("stargazers_count"),
                "forks": repo_data.get("forks_count"),
                "language": repo_data.get("language"),
                "languages": languages,
                "open_issues": repo_data.get("open_issues_count"),
                "topics": repo_data.get("topics", []),
                "url": repo_data.get("html_url"),
            }
            content_hash = hashlib.md5(str(signal_payload).encode()).hexdigest()

            try:
                signal = db.insert_raw_signal(
                    source="github",
                    external_id=str(repo_data.get("id", f"{owner}/{repo}")),
                    payload=signal_payload,
                    content_hash=content_hash
                )
                if signal:
                    db.insert_intelligence(
                        signal_id=signal["id"],
                        agent_name="RepoResearcher",
                        agent_version="3.0",
                        output_data={"summary": summary, "languages": languages}
                    )
            except Exception as e:
                print(f"[RepoResearcher] Supabase save warning: {e}")

            # Log audit event
            try:
                db.log_event(
                    component="RepoResearcher",
                    event_type="repo_analyzed",
                    message=f"Analyzed {owner}/{repo}",
                    metadata={"stars": repo_data.get("stargazers_count"), "language": repo_data.get("language")}
                )
            except Exception:
                pass

            self.log_trace(
                step_name="repo_analysis_complete",
                input_state={"owner": owner, "repo": repo},
                output_state={"summary_length": len(summary)}
            )

            return {"status": "success", "summary": summary}

        except httpx.TimeoutException:
            return {"status": "error", "summary": f"GitHub API timed out for {owner}/{repo}. Try again."}
        except Exception as e:
            return {"status": "error", "summary": f"Failed to analyze {owner}/{repo}: {str(e)}"}

    def _extract_repo_url(self, message: str) -> str:
        """Extract GitHub repo URL from user message."""
        url_match = re.search(r'github\.com/([\w.-]+/[\w.-]+)', message)
        if url_match:
            return f"https://github.com/{url_match.group(1)}"

        repo_match = re.search(r'([\w.-]+)/([\w.-]+)', message)
        if repo_match:
            return f"https://github.com/{repo_match.group(0)}"
        return ""

    def _parse_repo_url(self, url: str) -> tuple:
        """Parse owner and repo from URL."""
        parts = url.rstrip("/").split("/")
        if len(parts) >= 2:
            return parts[-2], parts[-1]
        return None, None

    def _generate_summary(self, owner, repo, data, languages, commits, readme):
        """Generate human-readable analysis from real GitHub data."""
        stars = data.get("stargazers_count", 0)
        forks = data.get("forks_count", 0)
        issues = data.get("open_issues_count", 0)
        desc = data.get("description", "No description")
        topics = data.get("topics", [])
        license_info = data.get("license", {})
        license_name = license_info.get("spdx_id", "Unknown") if license_info else "Unknown"
        created = data.get("created_at", "")[:10]
        updated = data.get("updated_at", "")[:10]

        s = f"## 🔍 Repository Analysis: [{owner}/{repo}]({data.get('html_url', '')})\n\n"
        s += f"**{desc}**\n\n"

        # Stats
        s += f"| Metric | Value |\n|--------|-------|\n"
        s += f"| ⭐ Stars | {stars:,} |\n"
        s += f"| 🍴 Forks | {forks:,} |\n"
        s += f"| 🐛 Open Issues | {issues:,} |\n"
        s += f"| 📜 License | {license_name} |\n"
        s += f"| 📅 Created | {created} |\n"
        s += f"| 🔄 Last Updated | {updated} |\n\n"

        # Languages
        if languages:
            total = sum(languages.values())
            s += "### 💻 Languages\n"
            for lang, bytes_count in sorted(languages.items(), key=lambda x: -x[1])[:8]:
                pct = (bytes_count / total) * 100
                bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
                s += f"- **{lang}**: {pct:.1f}% `{bar}`\n"
            s += "\n"

        # Topics
        if topics:
            s += "### 🏷️ Topics\n"
            s += " ".join(f"`{t}`" for t in topics[:10]) + "\n\n"

        # Recent commits
        if commits and isinstance(commits, list):
            s += "### 📝 Recent Commits\n"
            for c in commits[:5]:
                commit = c.get("commit", {})
                msg = commit.get("message", "").split("\n")[0][:80]
                author = commit.get("author", {}).get("name", "unknown")
                date = commit.get("author", {}).get("date", "")[:10]
                s += f"- `{date}` **{author}**: {msg}\n"
            s += "\n"

        # README preview
        if readme:
            s += "### 📖 README Preview\n"
            s += f"```\n{readme[:500]}\n```\n"

        return s
