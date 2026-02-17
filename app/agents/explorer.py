"""
Project Explorer Worker for DevPulseAI v3

Handles local file reading and project context queries.
Can read files, list directories, and analyze project structure.
"""

import os
import re
from typing import Dict, Any, List
from pathlib import Path
from app.core.swarm import Worker


class ProjectExplorer(Worker):
    """Worker that reads local files and project context."""
    
    # Safety: only allow reading from these roots
    ALLOWED_ROOTS = [
        "D:/DevPulseAIv2",
        "d:/DevPulseAIv2",
        "D:\\DevPulseAIv2",
        "d:\\DevPulseAIv2",
    ]
    
    # Files we can safely read (text-based)
    SAFE_EXTENSIONS = {
        ".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".md", ".txt",
        ".yaml", ".yml", ".toml", ".cfg", ".ini", ".env", ".sql",
        ".html", ".css", ".sh", ".bat", ".ps1", ".gitignore",
        ".dockerfile", ".csv"
    }
    
    def __init__(self):
        super().__init__(
            name="ProjectExplorer",
            capabilities=["file_read", "project_context", "directory_list"]
        )
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Read files or explore project structure.
        
        Expected task:
        {
            "user_message": "Read the content of README.md at D:/DevPulseAIv2/"
        }
        """
        user_message = task.get("user_message", "")
        
        self.log_trace(
            step_name="project_explorer_start",
            input_state={"message": user_message},
            output_state={}
        )
        
        # Try to extract a file path from the message
        file_path = self._extract_file_path(user_message)
        
        if file_path:
            return await self._read_file(file_path)
        
        # Try to extract a directory path
        dir_path = self._extract_directory_path(user_message)
        if dir_path:
            return await self._list_directory(dir_path)
        
        # Fallback: show project overview
        return await self._project_overview()
    
    def _extract_file_path(self, message: str) -> str:
        """Extract a file path from the user message."""
        # Pattern 1: Explicit path like D:/DevPulseAIv2/README.md
        path_match = re.search(r'([A-Za-z]:[/\\][\w./\\-]+\.\w+)', message)
        if path_match:
            return path_match.group(1)
        
        # Pattern 2: relative filename with directory context
        # e.g. "README.md present at D:/DevPulseAIv2/"
        file_match = re.search(r'([\w.-]+\.\w+)\s+(?:at|in|from|present at)\s+([A-Za-z]:[/\\][\w./\\-]+)', message)
        if file_match:
            filename = file_match.group(1)
            directory = file_match.group(2).rstrip("/\\")
            return f"{directory}/{filename}"
        
        # Pattern 3: Just a filename (assume project root)
        simple_file = re.search(r'\b([\w-]+\.(?:md|py|txt|json|yaml|yml|toml|js|ts))\b', message, re.IGNORECASE)
        if simple_file:
            return f"D:/DevPulseAIv2/{simple_file.group(1)}"
        
        return ""
    
    def _extract_directory_path(self, message: str) -> str:
        """Extract a directory path from the message."""
        dir_match = re.search(r'([A-Za-z]:[/\\][\w./\\-]+)/?', message)
        if dir_match:
            path = dir_match.group(1)
            if not '.' in Path(path).name:  # No extension = likely directory
                return path
        return ""
    
    def _is_safe_path(self, path: str) -> bool:
        """Check if the path is within allowed roots."""
        normalized = os.path.normpath(path).replace("\\", "/").lower()
        return any(
            normalized.startswith(root.replace("\\", "/").lower())
            for root in self.ALLOWED_ROOTS
        )
    
    async def _read_file(self, file_path: str) -> Dict[str, Any]:
        """Read and return file contents."""
        # Normalize the path
        file_path = os.path.normpath(file_path)
        
        # Security check
        if not self._is_safe_path(file_path):
            return {
                "status": "error",
                "summary": f"⛔ Cannot read files outside the project directory for security reasons."
            }
        
        if not os.path.exists(file_path):
            return {
                "status": "error",
                "summary": f"📁 File not found: `{file_path}`"
            }
        
        if not os.path.isfile(file_path):
            return await self._list_directory(file_path)
        
        # Check extension
        ext = Path(file_path).suffix.lower()
        if ext not in self.SAFE_EXTENSIONS:
            return {
                "status": "error",
                "summary": f"⚠️ Cannot read binary file type: `{ext}`"
            }
        
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            
            # Truncate if too long
            filename = Path(file_path).name
            if len(content) > 5000:
                content = content[:5000] + f"\n\n... (truncated, {len(content)} total characters)"
            
            summary = f"## 📄 {filename}\n\n"
            summary += f"**Path:** `{file_path}`\n"
            summary += f"**Size:** {os.path.getsize(file_path):,} bytes\n\n"
            summary += f"```{ext.lstrip('.')}\n{content}\n```"
            
            self.log_trace(
                step_name="file_read_complete",
                input_state={"path": file_path},
                output_state={"size": os.path.getsize(file_path)}
            )
            
            return {"status": "success", "summary": summary}
            
        except Exception as e:
            return {"status": "error", "summary": f"Error reading file: {e}"}
    
    async def _list_directory(self, dir_path: str) -> Dict[str, Any]:
        """List directory contents."""
        dir_path = os.path.normpath(dir_path)
        
        if not self._is_safe_path(dir_path):
            return {"status": "error", "summary": "⛔ Cannot access directories outside the project."}
        
        if not os.path.isdir(dir_path):
            return {"status": "error", "summary": f"Not a directory: `{dir_path}`"}
        
        try:
            entries = sorted(os.listdir(dir_path))
            dirs = []
            files = []
            
            for entry in entries:
                full = os.path.join(dir_path, entry)
                if os.path.isdir(full):
                    dirs.append(f"📁 {entry}/")
                else:
                    size = os.path.getsize(full)
                    files.append(f"📄 {entry} ({size:,} bytes)")
            
            summary = f"## 📂 Directory: {dir_path}\n\n"
            if dirs:
                summary += "**Folders:**\n" + "\n".join(f"- {d}" for d in dirs[:20]) + "\n\n"
            if files:
                summary += "**Files:**\n" + "\n".join(f"- {f}" for f in files[:30]) + "\n"
            
            if len(entries) > 50:
                summary += f"\n_... and {len(entries) - 50} more items_"
            
            return {"status": "success", "summary": summary}
            
        except Exception as e:
            return {"status": "error", "summary": f"Error listing directory: {e}"}
    
    async def _project_overview(self) -> Dict[str, Any]:
        """Show project overview when no specific file/dir requested."""
        root = "D:/DevPulseAIv2"
        result = await self._list_directory(root)
        
        if result["status"] == "success":
            result["summary"] = "## 🏗️ Project Overview\n\n" + result["summary"].split("\n\n", 1)[-1]
        
        return result
