import os
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, and_, String, cast

from app.tools.base import BaseTool
import app.db.session
from app.models.repository import Repository, SourceFile, CodeChunk
from app.models.incident import incident_repositories

class CodeSearchTool(BaseTool):
    name = "code_search"
    description = "Search indexed source code associated with the incident for relevant files, symbols, routes, configuration values and code text."
    input_schema = {
        "type": "object",
        "properties": {
            "incident_id": {"type": "string"},
            "repository_ids": {"type": "array", "items": {"type": "string"}},
            "query": {"type": "string"},
            "languages": {"type": "array", "items": {"type": "string"}},
            "path_prefix": {"type": "string"},
            "file_extensions": {"type": "array", "items": {"type": "string"}},
            "limit": {"type": "integer"}
        },
        "required": ["incident_id", "repository_ids", "query"]
    }

    async def _verify_repositories(self, db: AsyncSession, incident_id: str, repository_ids: List[str]) -> bool:
        """Verify that all requested repositories are associated with the incident."""
        if not repository_ids:
            return True
            
        result = await db.execute(
            select(incident_repositories.c.repository_id)
            .where(incident_repositories.c.incident_id == incident_id)
        )
        allowed_repo_ids = {row[0] for row in result.all()}
        
        for r_id in repository_ids:
            if r_id not in allowed_repo_ids:
                return False
        return True
        
    async def _get_all_incident_repositories(self, db: AsyncSession, incident_id: str) -> List[str]:
        result = await db.execute(
            select(incident_repositories.c.repository_id)
            .where(incident_repositories.c.incident_id == incident_id)
        )
        return [row[0] for row in result.all()]

    async def execute(self, **kwargs) -> Dict[str, Any]:
        incident_id = kwargs.get("incident_id")
        repository_ids = kwargs.get("repository_ids", [])
        query = kwargs.get("query", "")
        languages = kwargs.get("languages")
        path_prefix = kwargs.get("path_prefix")
        limit = kwargs.get("limit", 20)

        async with app.db.session.AsyncSessionLocal() as db:
            is_valid = await self._verify_repositories(db, incident_id, repository_ids)
            if not is_valid:
                return {"error": "One or more repository IDs are not associated with this incident."}
                
            if not repository_ids:
                repository_ids = await self._get_all_incident_repositories(db, incident_id)
                if not repository_ids:
                    return {"error": "No repositories associated with this incident."}
                
            query_words = [w.strip() for w in query.split() if w.strip()]
            
            stmt = (
                select(CodeChunk, SourceFile)
                .join(SourceFile, CodeChunk.source_file_id == SourceFile.id)
                .where(SourceFile.repository_id.in_(repository_ids))
            )
            
            if languages:
                stmt = stmt.where(SourceFile.language.in_(languages))
            if path_prefix:
                stmt = stmt.where(SourceFile.path.like(f"{path_prefix}%"))
                
            # All words must appear in either content, symbol_name or path
            if query_words:
                for word in query_words:
                    word_str = f"%{word}%"
                    stmt = stmt.where(
                        or_(
                            CodeChunk.content.ilike(word_str),
                            CodeChunk.symbol_name.ilike(word_str),
                            SourceFile.path.ilike(word_str)
                        )
                    )
            
            stmt = stmt.limit(limit)
            
            result = await db.execute(stmt)
            rows = result.all()
            
            results = []
            for chunk, sfile in rows:
                match_reasons = []
                match_reasons = ["keyword match"]
                
                results.append({
                    "repository_id": sfile.repository_id,
                    "file_path": sfile.path,
                    "language": sfile.language,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                    "symbol_name": chunk.symbol_name,
                    "snippet": chunk.content,
                    "content_hash": chunk.content_hash,
                    "match_reasons": match_reasons
                })
                
            return {
                "query": query,
                "total_matches": len(results),
                "returned_count": len(results),
                "results": results
            }
