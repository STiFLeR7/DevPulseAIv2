import httpx
import xml.etree.ElementTree as ET
from typing import List
from app.models.signal import Signal
from app.core.logger import logger

class ArXivAdapter:
    # ArXiv API is public and requires no key, but polite rate limiting.
    # Query: cat:cs.AI OR cat:cs.LG (AI & Machine Learning)
    BASE_URL = "https://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.LG&start=0&max_results=10&sortBy=submittedDate&sortOrder=descending"

    async def fetch_recent_papers(self) -> List[Signal]:
        signals = []
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.BASE_URL)
                response.raise_for_status()
                
                # ArXiv returns Atom/XML
                root = ET.fromstring(response.content)
                # Namespace handling usually required for Atom
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                
                for entry in root.findall('atom:entry', ns):
                    title = entry.find('atom:title', ns).text.strip()
                    summary = entry.find('atom:summary', ns).text.strip()
                    id_url = entry.find('atom:id', ns).text.strip()
                    link = entry.find("atom:link[@title='pdf']", ns)
                    pdf_link = link.attrib['href'] if link is not None else id_url
                    
                    published = entry.find('atom:published', ns).text
                    
                    signal = Signal(
                        source="arxiv",
                        external_id=id_url, # URI is unique ID
                        title=f"Paper: {title}",
                        content=f"Abstract: {summary}\nPublished: {published}",
                        url=id_url,
                        metadata={"pdf": pdf_link, "published": published}
                    )
                    signals.append(signal)

        except Exception as e:
            logger.error(f"ArXiv Adapter Error: {e}")
        
        return signals
