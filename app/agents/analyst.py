from typing import Dict, Any, List
from app.core.swarm import Worker

class PaperAnalyst(Worker):
    """Specialized agent for analyzing academic research papers."""
    
    def __init__(self):
        super().__init__(name="PaperAnalyst")
        
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze papers based on a research query.
        Expected task structure:
        {
            "user_message": "Find papers on RAG",
            "query": "retrieval augmented generation" (optional)
        }
        """
        user_message = task.get("user_message", "")
        query = task.get("query", user_message)  # Use message as query if not provided
        max_papers = task.get("max_papers", 3)
        
        if not query:
            return {
                "status": "error",
                "summary": "Please provide a research topic or query."
            }
        
        self.log_trace(
            step_name="paper_analysis_start",
            input_state={"query": query, "max_papers": max_papers},
            output_state={}
        )
        
        try:
            # 1. Search for relevant papers
            papers = await self._search_papers(query, max_papers)
            
            # 2. Generate summary
            summary = self._generate_summary(query, papers)
            
            self.log_trace(
                step_name="paper_analysis_complete",
                input_state={"query": query},
                output_state={"papers_found": len(papers), "summary": summary}
            )
            
            return {
                "status": "success",
                "summary": summary
            }
        except Exception as e:
            return {
                "status": "error",
                "summary": f"Failed to search papers: {str(e)}"
            }
    
    async def _search_papers(self, query: str, max_results: int) -> List[Dict]:
        """Search ArXiv for relevant papers."""
        # TODO: Use ArXiv API or web search with domain=arxiv.org
        # For now, return basic mock results
        return [
            {
                "title": f"Research on {query} - Paper {i+1}",
                "abstract": f"This paper explores {query} and proposes novel approaches.",
                "arxiv_id": f"2024.{i:05d}"
            }
            for i in range(max_results)
        ]
    
    def _generate_summary(self, query: str, papers: List[Dict]) -> str:
        """Generate human-readable summary of papers."""
        if not papers:
            return f"No papers found for query: '{query}'"
        
        summary = f"## Papers on: {query}\n\n"
        summary += f"Found {len(papers)} relevant papers:\n\n"
        
        for i, paper in enumerate(papers, 1):
            summary += f"**{i}. {paper['title']}**\n"
            summary += f"   - ArXiv ID: {paper['arxiv_id']}\n"
            summary += f"   - Abstract: {paper['abstract'][:100]}...\n\n"
        
        summary += "\n_ArXiv API integration coming soon for full paper analysis!_"
        
        return summary
