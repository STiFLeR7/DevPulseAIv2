"""
CommunityVibeAgent — Ephemeral Worker (SOW §3)

Analyzes community sentiment for a given topic by scanning
HackerNews and aggregating sentiment signals.

This is an ephemeral worker: spawned per-task, results returned, then GC'd.
"""

import re
from typing import Dict, Any, List

from app.core.swarm import Worker
from app.core.logger import logger


class CommunityVibeAgent(Worker):
    """
    Analyzes community sentiment around a technology or topic.

    Pulls from:
    - HackerNews (via adapter)
    - Internal signal store (Supabase raw_signals)

    Returns a structured sentiment summary:
    - Overall vibe: positive/neutral/negative
    - Key themes
    - Signal-to-noise ratio
    """

    # Sentiment lexicons (lightweight, no NLTK needed)
    POSITIVE_WORDS = {
        "amazing", "great", "excellent", "love", "fantastic", "impressive",
        "innovative", "breakthrough", "exciting", "powerful", "fast", "efficient",
        "elegant", "brilliant", "outstanding", "superb", "solid", "robust",
        "game-changer", "revolutionary", "incredible",
    }

    NEGATIVE_WORDS = {
        "terrible", "awful", "broken", "slow", "buggy", "bloated",
        "deprecated", "abandoned", "vulnerability", "exploit", "crash",
        "insecure", "overhyped", "disappointing", "unstable", "unusable",
        "fragile", "regression", "breaking", "failing",
    }

    def __init__(self):
        super().__init__(name="CommunityVibeAgent")

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze community sentiment for a topic.

        Task: {"user_message": "What's the community sentiment on Rust?"}
        """
        user_message = task.get("user_message", "")
        topic = self._extract_topic(user_message)

        if not topic:
            return {
                "status": "error",
                "summary": "I couldn't identify a topic to analyze. "
                           "Try: 'What's the community vibe on PyTorch?'"
            }

        self.log_trace(f"Analyzing community vibe for: {topic}")

        # Gather signals from multiple sources
        signals = await self._gather_signals(topic)

        if not signals:
            return {
                "status": "ok",
                "summary": f"No recent community signals found for '{topic}'. "
                           "This might be a niche topic or too new for community discussion.",
                "topic": topic,
                "signal_count": 0,
            }

        # Analyze sentiment
        analysis = self._analyze_sentiment(signals, topic)

        # Build response
        summary = self._build_summary(topic, analysis)

        return {
            "status": "ok",
            "summary": summary,
            "topic": topic,
            "signal_count": len(signals),
            "vibe": analysis["vibe"],
            "positive_ratio": analysis["positive_ratio"],
            "themes": analysis["themes"],
        }

    def _extract_topic(self, message: str) -> str:
        """Extract the topic to analyze from user message."""
        # Remove common prefixes
        for prefix in ["community vibe on", "sentiment on", "what do people think about",
                       "community opinion on", "vibe check on", "vibe on"]:
            if prefix in message.lower():
                topic = message.lower().split(prefix)[-1].strip().strip("?.")
                return topic

        # Fallback: use the main noun phrase
        words = message.split()
        # Skip common words
        skip = {"what", "is", "the", "on", "about", "how", "do", "people", "think", "community",
                "vibe", "sentiment", "check", "for", "of", "a", "an"}
        important = [w.strip("?.,!") for w in words if w.lower() not in skip and len(w) > 2]
        return " ".join(important) if important else ""

    async def _gather_signals(self, topic: str) -> List[Dict]:
        """Gather community signals from available sources."""
        signals = []

        # 1. Check HackerNews
        try:
            from app.adapters.hackernews import HackerNewsAdapter
            hn = HackerNewsAdapter()
            stories = await hn.fetch_stories(limit=30)
            topic_lower = topic.lower()
            for s in stories:
                text = f"{s.title} {s.content}".lower()
                if topic_lower in text or any(w in text for w in topic_lower.split()):
                    signals.append({
                        "source": "hackernews",
                        "title": s.title,
                        "content": s.content[:300],
                        "score": s.metadata.get("score", 0) if s.metadata else 0,
                    })
        except Exception as e:
            logger.warning(f"CommunityVibeAgent: HackerNews fetch failed: {e}")

        # 2. Check internal signals from Supabase
        try:
            from app.persistence.client import db
            stored = db.query_signals(limit=50)
            topic_lower = topic.lower()
            for sig in stored:
                payload = sig.get("payload", {})
                text = f"{payload.get('title', '')} {payload.get('content', '')}".lower()
                if topic_lower in text:
                    signals.append({
                        "source": sig.get("source", "internal"),
                        "title": payload.get("title", ""),
                        "content": payload.get("content", "")[:300],
                        "score": 1,
                    })
        except Exception as e:
            logger.warning(f"CommunityVibeAgent: Supabase query failed: {e}")

        return signals

    def _analyze_sentiment(self, signals: List[Dict], topic: str) -> Dict:
        """Simple lexicon-based sentiment analysis."""
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        themes = {}

        for sig in signals:
            text = f"{sig.get('title', '')} {sig.get('content', '')}".lower()
            words = set(text.split())

            pos = len(words & self.POSITIVE_WORDS)
            neg = len(words & self.NEGATIVE_WORDS)

            if pos > neg:
                positive_count += 1
            elif neg > pos:
                negative_count += 1
            else:
                neutral_count += 1

            # Extract themes (top repeated nouns)
            for word in words:
                if len(word) > 4 and word not in {"about", "other", "their", "there", "these", "those", "which", "would"}:
                    themes[word] = themes.get(word, 0) + 1

        total = len(signals)
        positive_ratio = positive_count / total if total > 0 else 0

        # Determine overall vibe
        if positive_ratio > 0.6:
            vibe = "positive"
        elif positive_ratio < 0.3:
            vibe = "negative"
        else:
            vibe = "mixed"

        # Top themes
        sorted_themes = sorted(themes.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "vibe": vibe,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "positive_ratio": round(positive_ratio, 2),
            "themes": [t[0] for t in sorted_themes],
        }

    def _build_summary(self, topic: str, analysis: Dict) -> str:
        """Build a human-readable sentiment summary."""
        vibe_emoji = {"positive": "🟢", "negative": "🔴", "mixed": "🟡"}
        emoji = vibe_emoji.get(analysis["vibe"], "⚪")

        summary = (
            f"{emoji} **Community Vibe: {topic}** — {analysis['vibe'].upper()}\n\n"
            f"Based on analysis of community signals:\n"
            f"- 👍 Positive: {analysis['positive_count']}\n"
            f"- 👎 Negative: {analysis['negative_count']}\n"
            f"- 😐 Neutral: {analysis['neutral_count']}\n\n"
        )

        if analysis["themes"]:
            summary += f"**Key themes**: {', '.join(analysis['themes'])}\n"

        return summary
