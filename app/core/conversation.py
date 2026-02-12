"""
Conversation Manager for DevPulseAI v3

Handles intent detection, context injection, and routing to appropriate agents.
Implements retry logic with exponential backoff for Gemini API rate limits.
"""

import os
import uuid
import asyncio
import time
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
from typing import Dict, List, Optional
from datetime import datetime, timezone
from enum import Enum

import google.generativeai as genai
from app.persistence.client import SupabaseManager
from app.core.swarm import SwarmManager, Message
from app.agents.researcher import RepoResearcher
from app.agents.analyst import PaperAnalyst
from app.agents.explorer import ProjectExplorer


class Intent(Enum):
    """User intent types."""
    REPO_ANALYSIS = "repo_analysis"
    PAPER_SEARCH = "paper_search"
    GENERAL_QA = "general_qa"
    PROJECT_CONTEXT = "project_context"


# Keyword patterns for fast local intent detection (no API call needed)
INTENT_KEYWORDS = {
    Intent.REPO_ANALYSIS: [
        "repo", "repository", "github", "analyze repo", "codebase",
        "code structure", "architecture of", "clone",
        "pull request", "commit history", "branch"
    ],
    Intent.PAPER_SEARCH: [
        "paper", "papers", "arxiv", "research paper", "study",
        "journal", "publication", "academic", "thesis", "survey"
    ],
    Intent.PROJECT_CONTEXT: [
        "read the content", "read file", "show file", "open file",
        "readme", "list directory", "list files", "show me",
        "project structure", "my project", "my stack", "my setup",
        "my code", "my dependencies", "my repo",
        "devpulseai", "requirements.txt", "package.json",
        ".env", ".py file", ".md file"
    ],
}


class ConversationManager:
    """
    Orchestrates conversations between users and the agent swarm.
    
    Responsibilities:
    - Classify user intent (keyword-first, Gemini fallback)
    - Inject relevant context (project deps, vector memory)
    - Route to appropriate workers via multiswarm dispatch
    - Handle API rate limits with exponential backoff
    - Read local project files via ProjectExplorer
    """
    
    # Retry configuration
    MAX_RETRIES = 3
    BASE_DELAY = 3.0  # seconds (increased from 2.0)
    
    def __init__(self, api_key: str = None):
        """Initialize conversation manager with multiswarm."""
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set. Please check your .env file.")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")
        
        self.db = SupabaseManager()
        self.swarm = SwarmManager()
        
        # Create domain-specific swarms (KimiK2.5 pattern)
        self.swarm.create_swarm("research", "Code & repository analysis")
        self.swarm.create_swarm("analysis", "Paper & data analysis")
        self.swarm.create_swarm("local", "Local project & file operations")
        
        # Register workers into their swarms
        self.swarm.register_worker(RepoResearcher(), swarm_name="research")
        self.swarm.register_worker(PaperAnalyst(), swarm_name="analysis")
        self.swarm.register_worker(ProjectExplorer(), swarm_name="local")
        
        self.conversation_id = str(uuid.uuid4())
        self._last_api_call = 0.0
    
    def _gemini_call_with_retry(self, prompt: str) -> str:
        """
        Call Gemini with exponential backoff on 429 rate limits.
        Delays: 3s → 6s → 12s between retries.
        """
        # Enforce minimum 1.5s gap between API calls
        elapsed = time.time() - self._last_api_call
        if elapsed < 1.5:
            time.sleep(1.5 - elapsed)
        
        for attempt in range(self.MAX_RETRIES):
            try:
                self._last_api_call = time.time()
                response = self.model.generate_content(prompt)
                return response.text
            except Exception as e:
                error_str = str(e)
                is_rate_limit = "429" in error_str or "Resource exhausted" in error_str
                
                if is_rate_limit and attempt < self.MAX_RETRIES - 1:
                    delay = self.BASE_DELAY * (2 ** attempt)  # 3s, 6s, 12s
                    print(f"[Gemini] Rate limited (attempt {attempt + 1}/{self.MAX_RETRIES}), retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    raise
    
    def detect_intent(self, user_message: str) -> Intent:
        """
        Classify user intent — keyword-first, Gemini fallback.
        
        Priority: local paths > keyword matching > Gemini API.
        """
        message_lower = user_message.lower()
        
        # Phase 0: Local path override — if the message contains a local
        # drive path (D:/, C:/ etc.), it's always a project context query,
        # even if it also contains "repo" or "github".
        import re
        has_local_path = bool(re.search(r'[a-z]:[/\\]', message_lower))
        if has_local_path and not ("github.com" in message_lower or "https://" in message_lower):
            print(f"[Intent] Local path detected → project_context")
            return Intent.PROJECT_CONTEXT
        
        # Phase 1: Fast keyword matching (no API call)
        for intent, keywords in INTENT_KEYWORDS.items():
            if any(kw in message_lower for kw in keywords):
                print(f"[Intent] Matched by keyword: {intent.value}")
                return intent
        
        # Phase 2: Gemini classification (with retry) for ambiguous messages
        prompt = f"""Classify the user's intent based on their message.

Available intents:
- repo_analysis: User wants to analyze a GitHub repository
- paper_search: User wants to find or summarize research papers  
- general_qa: General questions or chitchat
- project_context: Questions about local files, project setup, or directory contents

User message: "{user_message}"

Respond with ONLY the intent name, no explanation."""

        try:
            intent_str = self._gemini_call_with_retry(prompt).strip().lower()
            
            if "repo" in intent_str:
                return Intent.REPO_ANALYSIS
            elif "paper" in intent_str:
                return Intent.PAPER_SEARCH
            elif "project" in intent_str:
                return Intent.PROJECT_CONTEXT
            else:
                return Intent.GENERAL_QA
                
        except Exception as e:
            print(f"[Intent] Detection failed (using GENERAL_QA fallback): {e}")
            return Intent.GENERAL_QA
    
    def inject_context(self, user_message: str, intent: Intent) -> Dict:
        """Build enriched context for the agent."""
        return {
            "user_message": user_message,
            "intent": intent.value,
            "conversation_id": self.conversation_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def process_message(self, user_message: str) -> str:
        """
        Main entry point for processing user messages.
        
        Routes to specialized workers or Gemini directly.
        Handles rate limits gracefully with retry + user-friendly errors.
        """
        # 1. Detect intent
        intent = self.detect_intent(user_message)
        print(f"[ConversationManager] Intent: {intent.value}")
        
        # 2. Inject context
        context = self.inject_context(user_message, intent)
        
        # 3. Route to appropriate worker via multiswarm dispatch
        if intent == Intent.REPO_ANALYSIS:
            result = await self.swarm.dispatch("RepoResearcher", context)
            return result.get("summary", "No summary available.")
        
        elif intent == Intent.PAPER_SEARCH:
            result = await self.swarm.dispatch("PaperAnalyst", context)
            return result.get("summary", "No papers found.")
        
        elif intent == Intent.PROJECT_CONTEXT:
            result = await self.swarm.dispatch("ProjectExplorer", context)
            return result.get("summary", "Could not read project context.")
        
        elif intent == Intent.GENERAL_QA:
            try:
                response_text = self._gemini_call_with_retry(user_message)
                return response_text
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "Resource exhausted" in error_str:
                    return ("⏳ **Rate limit reached** — Gemini API is temporarily throttled.\n\n"
                            "Please wait ~15 seconds and try again, or try queries that "
                            "use local workers instead:\n"
                            "- 📂 `Read README.md` — reads local files\n"
                            "- 🔍 `Analyze owner/repo` — repo analysis\n"
                            "- 📄 `Find papers on topic` — paper search")
                return f"Sorry, I encountered an error: {e}"
        
        return "I'm not sure how to help with that yet."
    
    def save_message(self, role: str, content: str):
        """Save message to conversation history."""
        pass
    
    def get_conversation_history(self) -> List[Dict]:
        """Retrieve conversation history from database."""
        return []
