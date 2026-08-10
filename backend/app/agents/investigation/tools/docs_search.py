from typing import Dict, Any, List, Optional
import app.db.session
from app.tools.base import BaseTool
from app.services.retrieval_service import RetrievalService

class DocsSearchTool(BaseTool):
    name = "docs_search"
    description = "Search operational documentation, runbooks and service documentation associated with the incident using hybrid lexical and semantic retrieval."
    input_schema = {
        "type": "object",
        "properties": {
            "incident_id": {"type": "string"},
            "query": {"type": "string", "description": "The search query to match against documents."},
            "document_types": {
                "type": "array", 
                "items": {"type": "string"},
                "description": "Optional list of document types to filter by (e.g. RUNBOOK, TROUBLESHOOTING)."
            },
            "top_k": {"type": "integer", "description": "Number of chunks to return (default 5, max 15)"}
        },
        "required": ["incident_id", "query"]
    }

    def __init__(self):
        super().__init__()
        self.retrieval_service = RetrievalService()

    async def execute(self, **kwargs) -> Dict[str, Any]:
        incident_id = kwargs.get("incident_id")
        query = kwargs.get("query")
        document_types = kwargs.get("document_types")
        top_k = kwargs.get("top_k", 5)
        
        # Enforce limits
        top_k = min(max(1, top_k), 15)

        if not query or not query.strip():
            return {"error": "Query cannot be empty."}

        async with app.db.session.AsyncSessionLocal() as db:
            results = await self.retrieval_service.hybrid_search(
                db=db,
                query=query,
                incident_id=incident_id,
                document_types=document_types,
                top_k=top_k
            )

            # Format the output to limit the context window
            formatted_results = []
            for r in results:
                formatted_results.append({
                    "document_id": r["document_id"],
                    "title": r["title"],
                    "document_type": r["document_type"],
                    "section_title": r["section_title"],
                    "page_number": r["page_number"],
                    "chunk_id": r["chunk_id"],
                    "snippet": r["content"], # limit snippet if needed, but it's already chunked ~1k chars
                    "match_reasons": r.get("match_reasons", [])
                })

            return {
                "query": query,
                "returned_count": len(formatted_results),
                "results": formatted_results
            }
