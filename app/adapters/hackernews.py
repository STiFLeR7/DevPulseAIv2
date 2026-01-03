import httpx
from typing import List
from datetime import datetime
from app.models.signal import Signal
from app.core.logger import logger

class HackerNewsAdapter:
    """
    Adapter for Hacker News using the Algolia Search API.
    Focuses on stories related to AI, LLM, and Machine Learning.
    """
    # Algolia API is better for searching/filtering than the official Firebase API
    BASE_URL = "https://hn.algolia.com/api/v1/search_by_date"

    async def fetch_stories(self) -> List[Signal]:
        """
        Fetches recent high-signal stories from HN.
        """
        # Query for AI topics, stories only, with reasonable point threshold to reduce noise
        # Note: Algolia's numericFilters on points isn't always perfect on recent items, 
        # but 'search_by_date' gives us the newest. 
        # We'll filter strictly on client side if needed, but let's try to get a broad net first.
        query = "AI OR LLM OR Machine Learning OR OpenAI OR Gemini OR Llama"
        params = {
            "query": query,
            "tags": "story",
            "hitsPerPage": 20,
            "numericFilters": "points>5"
        }

        signals = []
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()

                for hit in data.get("hits", []):
                    # Skip if no URL (e.g. Ask HN often has no URL, but we might want them later. 
                    # For now, focus on external news).
                    if not hit.get("url") and not hit.get("story_text"):
                        continue
                    
                    # HN IDs are integers
                    external_id = str(hit.get("objectID"))
                    
                    content = f"""
Points: {hit.get('points', 0)}
Comments: {hit.get('num_comments', 0)}
Author: {hit.get('author')}
                    """.strip()

                    # Some hits have story_text (Ask HN)
                    if hit.get("story_text"):
                        content += f"\n\nText: {hit.get('story_text')}"

                    signal = Signal(
                        source="hackernews",
                        external_id=external_id,
                        title=hit.get("title", "Untitled HN Story"),
                        content=content,
                        url=hit.get("url") or f"https://news.ycombinator.com/item?id={external_id}",
                        metadata={
                            "points": hit.get("points"),
                            "comments": hit.get("num_comments"),
                            "author": hit.get("author")
                        }
                    )
                    signals.append(signal)
                    
        except Exception as e:
            logger.error(f"Hacker News Adapter Error: {e}")
            
        return signals
