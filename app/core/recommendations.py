"""
Proactive Recommendation Engine for DevPulseAI v3

Uses Pinecone (semantic search) + Supabase (recent signals/history)
to suggest relevant repos, papers, and topics.
"""

import os
from typing import List, Dict, Optional
from app.persistence.client import db


class RecommendationEngine:
    """
    Generates proactive recommendations by combining:
    1. User's recent conversation history (from Supabase)
    2. Semantic search in Pinecone knowledge index
    3. Trending signals from raw_signals table
    """

    def __init__(self):
        self._pinecone_index = None
        try:
            from pinecone import Pinecone
            pc_key = os.environ.get("PINECONE_API_KEY")
            if pc_key:
                pc = Pinecone(api_key=pc_key)
                self._pinecone_index = pc.Index("devpulseai-knowledge")
        except Exception:
            pass

    async def get_recommendations(self, conversation_id: Optional[str] = None, limit: int = 5) -> List[Dict]:
        """
        Generate recommendations based on user's recent activity.
        
        Flow:
        1. Get recent user queries from conversations table
        2. Search Pinecone for semantically similar content
        3. Get trending signals from raw_signals
        4. Merge, deduplicate, and rank
        """
        recommendations = []

        # --- 1. User interest extraction from recent conversations ---
        user_queries = []
        if conversation_id:
            try:
                history = db.get_conversations(conversation_id, limit=10)
                user_queries = [
                    msg["content"] for msg in history
                    if msg.get("role") == "user"
                ]
            except Exception:
                pass

        # --- 2. Pinecone semantic search for related knowledge ---
        if self._pinecone_index and user_queries:
            try:
                # Use the most recent query as the search seed
                seed_query = user_queries[-1] if user_queries else "trending AI tools"
                
                results = self._pinecone_index.search(
                    namespace="signals",
                    query={"inputs": {"text": seed_query}, "top_k": limit * 2},
                )
                
                hits = results.get("result", {}).get("hits", [])
                for hit in hits[:limit]:
                    fields = hit.get("fields", {})
                    recommendations.append({
                        "type": "semantic",
                        "source": fields.get("source", "knowledge"),
                        "content": fields.get("content", "")[:200],
                        "score": hit.get("_score", 0),
                        "reason": f"Related to: '{seed_query[:50]}'"
                    })
            except Exception as e:
                print(f"[Recommendations] Pinecone search warning: {e}")

        # --- 3. Trending signals from Supabase ---
        try:
            recent_signals = db.query_signals(limit=10)
            for sig in recent_signals:
                payload = sig.get("payload", {})
                title = payload.get("title", "")
                source = sig.get("source", "unknown")
                
                # Skip if already in recommendations
                if any(title and title[:30] in r.get("content", "") for r in recommendations):
                    continue
                
                recommendations.append({
                    "type": "trending",
                    "source": source,
                    "content": title or str(payload)[:200],
                    "score": 0.5,
                    "reason": f"Trending from {source}",
                    "url": payload.get("url") or payload.get("html_url", ""),
                })
        except Exception as e:
            print(f"[Recommendations] Supabase query warning: {e}")

        # --- 4. Deduplicate and sort by score ---
        seen = set()
        unique = []
        for r in recommendations:
            key = r["content"][:50]
            if key not in seen:
                seen.add(key)
                unique.append(r)

        unique.sort(key=lambda x: x.get("score", 0), reverse=True)
        return unique[:limit]
