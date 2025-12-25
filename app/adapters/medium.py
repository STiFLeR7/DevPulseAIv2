import feedparser
from typing import List
from app.models.signal import Signal
from app.core.logger import logger

class MediumAdapter:
    # Example feeds - in production this might be configurable via DB
    FEEDS = [
        "https://medium.com/feed/tag/artificial-intelligence",
        "https://medium.com/feed/tag/machine-learning",
        "https://openai.com/blog/rss.xml",
        "https://github.blog/feed/"
    ]

    async def fetch_feed_updates(self) -> List[Signal]:
        signals = []
        for feed_url in self.FEEDS:
            try:
                # feedparser is blocking, so strictly speaking should be run in executor if async
                # keeping it simple here for the initial implementation
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:5]: # Top 5 per feed
                    summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
                    signal = Signal(
                        source="medium_rss",
                        external_id=entry.link,
                        title=entry.title,
                        content=f"Summary: {summary[:1000]}...", # Truncate for now
                        url=entry.link,
                        metadata={"published": getattr(entry, "published", "")}
                    )
                    signals.append(signal)
            except Exception as e:
                logger.error(f"RSS Adapter Error ({feed_url}): {e}")
        
        return signals
