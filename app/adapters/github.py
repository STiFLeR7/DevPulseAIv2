import os
import httpx
from typing import List
from datetime import datetime, timedelta
from app.models.signal import Signal
from app.core.logger import logger

class GitHubAdapter:
    BASE_URL = "https://api.github.com"

    def __init__(self):
        self.token = os.environ.get("GITHUB_TOKEN")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json"
        } if self.token else {}

    async def fetch_trending(self) -> List[Signal]:
        """
        Fetches trending repositories (simulated via search api due to lack of public trending api).
        """
        # Search for high star count repos created continuously or pushed recently could simulate trending
        # For 'trending' exactly, we often need to scrape github.com/trending or use third party.
        # Here we use search for top repos active in last 24h.
        
        date_query = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        query = f"created:>{date_query} sort:stars"
        
        url = f"{self.BASE_URL}/search/repositories?q={query}&per_page=10"
        
        signals = []
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                
                for item in data.get("items", []):
                    signal = Signal(
                        source="github",
                        external_id=str(item["id"]),
                        title=f"Trending Repo: {item['full_name']}",
                        content=f"Description: {item['description']}\nStars: {item['stargazers_count']}\nLanguage: {item['language']}",
                        url=item["html_url"],
                        metadata=item
                    )
                    signals.append(signal)

        except Exception as e:
            logger.error(f"GitHub Adapter Error: {e}")
        
        return signals
