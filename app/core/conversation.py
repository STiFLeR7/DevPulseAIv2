"""
Conversation Manager for DevPulseAI v3

Handles intent detection, context injection, routing to agents,
and persists ALL data to Supabase (conversations, audit_logs, raw_signals)
and Pinecone (knowledge vectors).
"""

import os
import uuid
import asyncio
import time
import hashlib
from enum import Enum
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

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
    ],
    Intent.PAPER_SEARCH: [
        "paper", "papers", "arxiv", "research", "academic",
        "publication", "study", "literature", "survey",
    ],
    Intent.PROJECT_CONTEXT: [
        "read file", "show file", "directory", "tree", "local",
        "project structure", "my project", "my stack", "my setup",
        "my code", "my dependencies", "my repo",
        "devpulseai", "requirements.txt", "package.json",
        ".env", ".py file", ".md file",
    ],
}


class ConversationManager:
    """
    Orchestrates conversations between users and the agent swarm.
    
    Now persists ALL interactions to Supabase:
    - conversations table: full chat history
    - audit_logs: every query/response event
    - raw_signals + processed_intelligence: agent results
    - user_feedback: thumbs up/down from UI
    
    Also stores knowledge vectors in Pinecone.
    """
    
    MAX_RETRIES = 3
    BASE_DELAY = 3.0
    
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

        # Pinecone integration (optional — only if configured)
        self._pinecone_index = None
        try:
            from pinecone import Pinecone
            pc_key = os.environ.get("PINECONE_API_KEY")
            if pc_key:
                pc = Pinecone(api_key=pc_key)
                self._pinecone_index = pc.Index("devpulseai-knowledge")
                print("[ConversationManager] Pinecone connected.")
        except Exception:
            pass  # Pinecone is optional

    def _gemini_call_with_retry(self, prompt: str) -> str:
        """
        Call Gemini with exponential backoff on 429 rate limits.
        Delays: 3s -> 6s -> 12s between retries.
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                # Enforce minimum gap between API calls
                now = time.time()
                elapsed = now - self._last_api_call
                if elapsed < 1.0:
                    time.sleep(1.0 - elapsed)
                
                response = self.model.generate_content(prompt)
                self._last_api_call = time.time()
                return response.text
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "Resource exhausted" in error_str:
                    delay = self.BASE_DELAY * (2 ** attempt)
                    if attempt < self.MAX_RETRIES - 1:
                        print(f"[Gemini] Rate limited (attempt {attempt+1}/{self.MAX_RETRIES}), retrying in {delay}s...")
                        time.sleep(delay)
                        continue
                raise

    def detect_intent(self, user_message: str) -> Intent:
        """
        Classify user intent — keyword-first, Gemini fallback.
        Priority: local paths > keyword matching > Gemini API.
        """
        lower = user_message.lower()
        
        # Priority 1: Local file paths (Windows/Unix)
        import re
        if re.search(r'[A-Za-z]:[/\\]', user_message) or re.search(r'/home/', user_message):
            print(f"[Intent] Local path detected -> project_context")
            return Intent.PROJECT_CONTEXT
        
        # Priority 2: Keyword matching (fast, no API call)
        for intent, keywords in INTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in lower:
                    print(f"[Intent] Matched by keyword: {intent.value}")
                    return intent
        
        # Priority 3: Gemini classification (fallback, uses API)
        try:
            prompt = (
                "Classify this user message into exactly ONE category:\n"
                "- repo_analysis (about GitHub repos, code analysis)\n"
                "- paper_search (about research papers, academic)\n"
                "- project_context (about local files, project setup)\n"
                "- general_qa (general questions)\n\n"
                f"Message: {user_message}\n\n"
                "Reply with ONLY the category name, nothing else."
            )
            result = self._gemini_call_with_retry(prompt).strip().lower()
            
            intent_map = {
                "repo_analysis": Intent.REPO_ANALYSIS,
                "paper_search": Intent.PAPER_SEARCH,
                "project_context": Intent.PROJECT_CONTEXT,
                "general_qa": Intent.GENERAL_QA,
            }
            return intent_map.get(result, Intent.GENERAL_QA)
        except Exception:
            return Intent.GENERAL_QA

    def inject_context(self, user_message: str, intent: Intent) -> Dict:
        """Build enriched context for the agent."""
        return {
            "user_message": user_message,
            "intent": intent.value,
            "conversation_id": self.conversation_id,
        }

    async def process_message(self, user_message: str) -> str:
        """
        Main entry point for processing user messages.
        
        Routes to specialized workers or Gemini directly.
        Persists EVERYTHING to Supabase.
        """
        start_time = time.time()
        
        # 1. Detect intent
        intent = self.detect_intent(user_message)
        print(f"[ConversationManager] Intent: {intent.value}")
        
        # 2. Save user message to Supabase
        self.save_message("user", user_message, intent=intent.value)
        
        # 3. Inject context
        context = self.inject_context(user_message, intent)
        
        # 4. Route to appropriate worker
        response = ""
        try:
            if intent == Intent.REPO_ANALYSIS:
                result = await self.swarm.dispatch("RepoResearcher", context)
                response = result.get("summary", "No summary available.")
            
            elif intent == Intent.PAPER_SEARCH:
                result = await self.swarm.dispatch("PaperAnalyst", context)
                response = result.get("summary", "No papers found.")
            
            elif intent == Intent.PROJECT_CONTEXT:
                result = await self.swarm.dispatch("ProjectExplorer", context)
                response = result.get("summary", "Could not read project context.")
            
            elif intent == Intent.GENERAL_QA:
                try:
                    response = self._gemini_call_with_retry(user_message)
                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str or "Resource exhausted" in error_str:
                        response = (
                            "⏳ **Rate limit reached** — Gemini API is temporarily throttled.\n\n"
                            "Please wait ~15 seconds and try again, or try queries that "
                            "use local workers instead:\n"
                            "- 📂 `Read README.md` — reads local files\n"
                            "- 🔍 `Analyze owner/repo` — repo analysis\n"
                            "- 📄 `Find papers on topic` — paper search"
                        )
                    else:
                        response = f"Sorry, I encountered an error: {e}"
            
            else:
                response = "I'm not sure how to help with that yet."
        except Exception as e:
            response = f"An error occurred: {str(e)}"
        
        elapsed = time.time() - start_time
        
        # 5. Save assistant response to Supabase
        self.save_message("assistant", response, intent=intent.value, metadata={
            "latency_ms": int(elapsed * 1000),
            "intent": intent.value,
        })
        
        # 6. Log to audit_logs
        try:
            self.db.log_event(
                component="ConversationManager",
                event_type="message_processed",
                message=f"Intent: {intent.value} | Latency: {elapsed:.1f}s",
                metadata={
                    "conversation_id": self.conversation_id,
                    "intent": intent.value,
                    "query_preview": user_message[:100],
                    "response_length": len(response),
                    "latency_ms": int(elapsed * 1000),
                }
            )
        except Exception as e:
            print(f"[ConversationManager] Audit log warning: {e}")
        
        # 7. Store in Pinecone for knowledge retrieval (async, non-blocking)
        self._store_in_pinecone(user_message, response, intent.value)
        
        return response
    
    def save_message(self, role: str, content: str, intent: str = None, metadata: dict = None):
        """Save message to conversations table in Supabase."""
        try:
            self.db.insert_conversation(
                conversation_id=self.conversation_id,
                role=role,
                content=content,
                intent=intent,
                metadata=metadata
            )
        except Exception as e:
            print(f"[ConversationManager] Save message warning: {e}")
    
    def get_conversation_history(self) -> List[Dict]:
        """Retrieve conversation history from Supabase."""
        try:
            return self.db.get_conversations(self.conversation_id)
        except Exception:
            return []

    def _store_in_pinecone(self, query: str, response: str, intent: str):
        """Store Q&A pair in Pinecone for future knowledge retrieval."""
        if not self._pinecone_index:
            return
        try:
            record_id = hashlib.md5(f"{query}:{self.conversation_id}".encode()).hexdigest()
            self._pinecone_index.upsert_records(
                namespace="conversations",
                records=[{
                    "_id": record_id,
                    "content": f"Q: {query}\nA: {response[:500]}",
                    "intent": intent,
                    "conversation_id": self.conversation_id,
                }]
            )
        except Exception as e:
            print(f"[Pinecone] Store warning: {e}")
