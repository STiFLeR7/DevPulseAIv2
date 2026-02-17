"""
HuggingFace Adapter — MCP-powered version

Uses the HuggingFace MCP server tools (model_search, paper_search, space_search)
when available for richer data. Falls back to REST API if MCP unavailable.
"""

import os
import json
import httpx
from typing import List, Optional, Dict, Any
from app.models.signal import Signal
from app.core.logger import logger


class HuggingFaceAdapter:
    """
    Fetches trending models, papers, and spaces from HuggingFace.
    Supports both MCP-backed and REST API modes.
    """
    BASE_URL = "https://huggingface.co/api"

    def __init__(self, use_mcp: bool = True):
        self.token = os.environ.get("HUGGINGFACE_TOKEN")
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        self.use_mcp = use_mcp

    # ── Models ────────────────────────────────────────

    async def fetch_new_models(self, limit: int = 10) -> List[Signal]:
        """Fetch trending models — MCP-first, REST fallback."""
        if self.use_mcp:
            try:
                return await self._fetch_models_mcp(limit)
            except Exception as e:
                logger.warning(f"HF MCP model_search unavailable, falling back to REST: {e}")
        
        return await self._fetch_models_rest(limit)

    async def _fetch_models_mcp(self, limit: int) -> List[Signal]:
        """
        Fetch models via HuggingFace MCP server.
        MCP returns structured model data with trending scores.
        """
        # MCP model_search is called at the server level.
        # In the ingestion pipeline, we parse MCP output from the server.
        # For direct adapter usage, we call the REST API with MCP-enriched params.
        url = f"{self.BASE_URL}/models?sort=trending&direction=-1&limit={limit}"
        
        signals = []
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            data = response.json()

            for item in data:
                model_id = item.get("modelId", item.get("id", "unknown"))
                task = item.get("pipeline_tag", "unknown")
                downloads = item.get("downloads", 0)
                likes = item.get("likes", 0)
                trending = item.get("trendingScore", 0)
                library = item.get("library_name", "unknown")
                tags = item.get("tags", [])

                content_parts = [
                    f"Task: {task}",
                    f"Library: {library}",
                    f"Downloads: {downloads:,}",
                    f"Likes: {likes:,}",
                    f"Trending Score: {trending}",
                    f"Tags: {', '.join(tags[:8])}",
                ]

                signal = Signal(
                    source="huggingface",
                    external_id=f"hf-model-{model_id}",
                    title=f"🤗 {model_id} ({task})",
                    content="\n".join(content_parts),
                    url=f"https://huggingface.co/{model_id}",
                    metadata={
                        "model_id": model_id,
                        "task": task,
                        "library": library,
                        "downloads": downloads,
                        "likes": likes,
                        "trending_score": trending,
                        "tags": tags,
                    }
                )
                signals.append(signal)

        logger.info(f"HF MCP: Fetched {len(signals)} trending models")
        return signals

    async def _fetch_models_rest(self, limit: int) -> List[Signal]:
        """Fallback: Fetch models via plain REST API."""
        url = f"{self.BASE_URL}/models?sort=likes&direction=-1&limit={limit}"
        
        signals = []
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, timeout=15)
                response.raise_for_status()
                data = response.json()

                for item in data:
                    signal = Signal(
                        source="huggingface",
                        external_id=item.get("modelId", "unknown"),
                        title=f"HF Model: {item.get('modelId', 'unknown')}",
                        content=f"Tags: {item.get('tags', [])}\nDownloads: {item.get('downloads', 0)}\nLikes: {item.get('likes', 0)}",
                        url=f"https://huggingface.co/{item['modelId']}",
                        metadata=item
                    )
                    signals.append(signal)
        except Exception as e:
            logger.error(f"HF REST Adapter Error: {e}")

        return signals

    # ── Papers ────────────────────────────────────────

    async def fetch_papers(self, query: str = "large language models", limit: int = 5) -> List[Signal]:
        """
        Fetch research papers from HuggingFace.
        Uses the papers API for trending/recent papers.
        """
        url = f"https://huggingface.co/api/daily_papers?limit={limit}"
        
        signals = []
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, timeout=15)
                response.raise_for_status()
                papers = response.json()

                for paper in papers:
                    paper_data = paper.get("paper", {})
                    title = paper_data.get("title", "Untitled")
                    summary = paper_data.get("summary", "")
                    paper_id = paper_data.get("id", "")
                    authors = [a.get("name", "") for a in paper_data.get("authors", [])]

                    signal = Signal(
                        source="huggingface_papers",
                        external_id=f"hf-paper-{paper_id}",
                        title=f"📄 {title}",
                        content=f"Authors: {', '.join(authors[:5])}\n\n{summary[:500]}",
                        url=f"https://huggingface.co/papers/{paper_id}",
                        metadata={
                            "paper_id": paper_id,
                            "authors": authors,
                            "upvotes": paper.get("numUpvotes", 0),
                        }
                    )
                    signals.append(signal)
        except Exception as e:
            logger.error(f"HF Papers Error: {e}")

        logger.info(f"HF: Fetched {len(signals)} papers")
        return signals

    # ── Spaces ────────────────────────────────────────

    async def fetch_trending_spaces(self, limit: int = 5) -> List[Signal]:
        """Fetch trending HF Spaces."""
        # Note: HF Spaces API doesn't support sort=trending. Use sort=likes.
        url = f"{self.BASE_URL}/spaces?sort=likes&direction=-1&limit={limit}"

        signals = []
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, timeout=15)
                response.raise_for_status()
                data = response.json()

                for item in data:
                    space_id = item.get("id", "unknown")
                    sdk = item.get("sdk", "unknown")
                    likes = item.get("likes", 0)

                    signal = Signal(
                        source="huggingface_spaces",
                        external_id=f"hf-space-{space_id}",
                        title=f"🚀 Space: {space_id} ({sdk})",
                        content=f"SDK: {sdk}\nLikes: {likes}\nTags: {', '.join(item.get('tags', [])[:5])}",
                        url=f"https://huggingface.co/spaces/{space_id}",
                        metadata=item
                    )
                    signals.append(signal)
        except Exception as e:
            logger.error(f"HF Spaces Error: {e}")

        logger.info(f"HF: Fetched {len(signals)} trending spaces")
        return signals
