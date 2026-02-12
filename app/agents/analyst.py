"""
PaperAnalyst — ArXiv Paper Search & Analysis Agent

Uses the real ArXiv API to search for academic papers by query.
Stores results as raw_signals in Supabase.
"""

import hashlib
import httpx
import xml.etree.ElementTree as ET
from typing import Dict, Any, List

from app.core.swarm import Worker
from app.persistence.client import db


class PaperAnalyst(Worker):
    """Specialized agent for searching and analyzing academic papers via ArXiv."""

    ARXIV_API = "https://export.arxiv.org/api/query"

    def __init__(self):
        super().__init__(name="PaperAnalyst")

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search ArXiv for papers matching a research query.
        Expected task: {"user_message": "Find papers on RAG"}
        """
        user_message = task.get("user_message", "")
        query = task.get("query", user_message)
        max_papers = task.get("max_papers", 5)

        if not query:
            return {"status": "error", "summary": "Please provide a research topic or query."}

        self.log_trace(
            step_name="paper_search_start",
            input_state={"query": query, "max_papers": max_papers},
            output_state={}
        )

        try:
            papers = await self._search_arxiv(query, max_papers)

            if not papers:
                return {"status": "success", "summary": f"No papers found for: '{query}'"}

            summary = self._generate_summary(query, papers)

            # Persist each paper to Supabase
            for paper in papers:
                try:
                    content_hash = hashlib.md5(paper["arxiv_id"].encode()).hexdigest()
                    signal = db.insert_raw_signal(
                        source="arxiv",
                        external_id=paper["arxiv_id"],
                        payload={
                            "title": paper["title"],
                            "abstract": paper["abstract"],
                            "authors": paper["authors"],
                            "published": paper["published"],
                            "pdf_url": paper["pdf_url"],
                            "categories": paper["categories"],
                        },
                        content_hash=content_hash
                    )
                    if signal:
                        db.insert_intelligence(
                            signal_id=signal["id"],
                            agent_name="PaperAnalyst",
                            agent_version="3.0",
                            output_data={"title": paper["title"], "relevance_query": query}
                        )
                except Exception as e:
                    print(f"[PaperAnalyst] Supabase save warning: {e}")

            # Log audit event
            try:
                db.log_event(
                    component="PaperAnalyst",
                    event_type="papers_searched",
                    message=f"Found {len(papers)} papers for '{query[:50]}'",
                    metadata={"query": query, "count": len(papers)}
                )
            except Exception:
                pass

            self.log_trace(
                step_name="paper_search_complete",
                input_state={"query": query},
                output_state={"papers_found": len(papers)}
            )

            return {"status": "success", "summary": summary}

        except httpx.TimeoutException:
            return {"status": "error", "summary": "ArXiv API timed out. Please try again."}
        except Exception as e:
            return {"status": "error", "summary": f"Failed to search papers: {str(e)}"}

    async def _search_arxiv(self, query: str, max_results: int) -> List[Dict]:
        """Search ArXiv API for papers matching the query."""
        import urllib.parse
        
        # Strip stopwords to get meaningful search terms
        stopwords = {"find", "search", "papers", "paper", "on", "about", "the", "a", "an",
                      "for", "in", "of", "to", "and", "or", "with", "by", "from", "recent",
                      "latest", "new", "tell", "me", "show", "get", "what", "is", "are"}
        words = [w for w in query.lower().split() if w not in stopwords and len(w) > 1]
        
        if not words:
            words = query.lower().split()[:3]  # Fallback to first 3 words
        
        # Use ArXiv search syntax: ti = title, abs = abstract
        # Combine with AND for precision, limit to 5 terms max
        terms = words[:5]
        search_parts = [f"all:{urllib.parse.quote(term)}" for term in terms]
        search_query = "+AND+".join(search_parts)
        
        url = (
            f"{self.ARXIV_API}?search_query={search_query}"
            f"&start=0&max_results={max_results}"
            f"&sortBy=relevance&sortOrder=descending"
        )

        papers = []
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            response.raise_for_status()

            root = ET.fromstring(response.content)
            ns = {"atom": "http://www.w3.org/2005/Atom"}

            for entry in root.findall("atom:entry", ns):
                title_el = entry.find("atom:title", ns)
                summary_el = entry.find("atom:summary", ns)
                id_el = entry.find("atom:id", ns)
                published_el = entry.find("atom:published", ns)

                if title_el is None or id_el is None:
                    continue

                title = " ".join(title_el.text.strip().split())
                abstract = " ".join(summary_el.text.strip().split()) if summary_el is not None else ""
                arxiv_id = id_el.text.strip()
                published = published_el.text.strip() if published_el is not None else ""

                # Get authors
                authors = []
                for author in entry.findall("atom:author", ns):
                    name_el = author.find("atom:name", ns)
                    if name_el is not None:
                        authors.append(name_el.text.strip())

                # Get PDF link
                pdf_url = arxiv_id
                pdf_link = entry.find("atom:link[@title='pdf']", ns)
                if pdf_link is not None:
                    pdf_url = pdf_link.attrib.get("href", arxiv_id)

                # Get categories
                categories = []
                for cat in entry.findall("{http://arxiv.org/schemas/atom}primary_category"):
                    categories.append(cat.attrib.get("term", ""))

                papers.append({
                    "title": title,
                    "abstract": abstract,
                    "arxiv_id": arxiv_id,
                    "authors": authors,
                    "published": published[:10],
                    "pdf_url": pdf_url,
                    "categories": categories,
                })

        return papers

    def _generate_summary(self, query: str, papers: List[Dict]) -> str:
        """Generate human-readable summary of papers found."""
        s = f"## 📄 ArXiv Papers: \"{query}\"\n\n"
        s += f"Found **{len(papers)}** relevant papers:\n\n"

        for i, p in enumerate(papers, 1):
            authors_str = ", ".join(p["authors"][:3])
            if len(p["authors"]) > 3:
                authors_str += f" et al. ({len(p['authors'])} authors)"

            s += f"### {i}. {p['title']}\n"
            s += f"**Authors:** {authors_str}\n"
            s += f"**Published:** {p['published']}\n"
            s += f"**ArXiv:** [{p['arxiv_id']}]({p['arxiv_id']})\n"
            if p.get("pdf_url"):
                s += f"**PDF:** [{p['pdf_url'].split('/')[-1]}]({p['pdf_url']})\n"
            s += f"\n> {p['abstract'][:300]}{'...' if len(p['abstract']) > 300 else ''}\n\n"
            s += "---\n\n"

        return s
