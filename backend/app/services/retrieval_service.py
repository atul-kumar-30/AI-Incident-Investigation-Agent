import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text, or_

from app.models.document import Document, DocumentChunk, DocumentType
from app.models.incident import incident_documents
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class RetrievalService:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.rrf_k = 60  # Configurable RRF constant

    async def hybrid_search(self, 
                            db: AsyncSession, 
                            query: str, 
                            incident_id: Optional[str] = None, 
                            document_types: Optional[List[str]] = None,
                            top_k: int = 5) -> List[Dict[str, Any]]:
        
        # 1. Semantic Candidates
        query_embedding = await self.embedding_service.embed_query(query)
        semantic_candidates = await self._get_semantic_candidates(db, query_embedding, incident_id, document_types, top_k * 2)
        
        # 2. Lexical Candidates
        lexical_candidates = await self._get_lexical_candidates(db, query, incident_id, document_types, top_k * 2)
        
        # 3. Reciprocal Rank Fusion (RRF)
        fused_results = self._fuse_results(semantic_candidates, lexical_candidates)
        
        # 4. Diversity/Deduplication (Avoid returning many adjacent chunks from same document)
        diverse_results = self._apply_diversity(fused_results, top_k)
        
        return diverse_results

    async def _get_semantic_candidates(self, db: AsyncSession, query_embedding: List[float], incident_id: Optional[str], document_types: Optional[List[str]], limit: int) -> List[Dict[str, Any]]:
        """Retrieves using pgvector cosine distance (<=>)."""
        # We need to compute cosine distance and sort by it
        stmt = (
            select(DocumentChunk, Document)
            .join(Document, DocumentChunk.document_id == Document.id)
        )
        
        if incident_id:
            # We allow docs associated with the incident OR docs that are GENERAL/RUNBOOK available to all
            stmt = stmt.outerjoin(incident_documents, Document.id == incident_documents.c.document_id).where(
                or_(
                    incident_documents.c.incident_id == incident_id,
                    Document.document_type.in_([DocumentType.RUNBOOK, DocumentType.GENERAL])
                )
            )
            
        if document_types:
            stmt = stmt.where(Document.document_type.in_(document_types))
            
        # Order by cosine distance ( <=> )
        stmt = stmt.order_by(DocumentChunk.embedding.cosine_distance(query_embedding)).limit(limit)
        
        result = await db.execute(stmt)
        candidates = []
        for i, (chunk, doc) in enumerate(result.all()):
            candidates.append({
                "chunk_id": chunk.id,
                "document_id": doc.id,
                "title": doc.title,
                "document_type": doc.document_type,
                "section_title": chunk.section_title,
                "page_number": chunk.page_number,
                "content": chunk.content,
                "chunk_index": chunk.chunk_index,
                "content_hash": chunk.content_hash,
                "semantic_rank": i + 1
            })
            
        return candidates

    async def _get_lexical_candidates(self, db: AsyncSession, query: str, incident_id: Optional[str], document_types: Optional[List[str]], limit: int) -> List[Dict[str, Any]]:
        """Retrieves using basic ILIKE / text search."""
        # Using ILIKE for simplicity, ideally tsvector full-text search
        words = [w for w in query.split() if w.strip()]
        if not words:
            return []
            
        stmt = (
            select(DocumentChunk, Document)
            .join(Document, DocumentChunk.document_id == Document.id)
        )
        
        if incident_id:
            stmt = stmt.outerjoin(incident_documents, Document.id == incident_documents.c.document_id).where(
                or_(
                    incident_documents.c.incident_id == incident_id,
                    Document.document_type.in_([DocumentType.RUNBOOK, DocumentType.GENERAL])
                )
            )
            
        if document_types:
            stmt = stmt.where(Document.document_type.in_(document_types))
            
        # Basic ILIKE matching for words
        conditions = [DocumentChunk.content.ilike(f"%{w}%") for w in words]
        stmt = stmt.where(or_(*conditions)).limit(limit)
        
        result = await db.execute(stmt)
        candidates = []
        for i, (chunk, doc) in enumerate(result.all()):
            candidates.append({
                "chunk_id": chunk.id,
                "document_id": doc.id,
                "title": doc.title,
                "document_type": doc.document_type,
                "section_title": chunk.section_title,
                "page_number": chunk.page_number,
                "content": chunk.content,
                "chunk_index": chunk.chunk_index,
                "content_hash": chunk.content_hash,
                "lexical_rank": i + 1
            })
            
        return candidates

    def _fuse_results(self, semantic: List[Dict[str, Any]], lexical: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Implements Reciprocal Rank Fusion."""
        chunk_map = {}
        
        def _add_to_map(candidates, rank_key):
            for c in candidates:
                c_id = c["chunk_id"]
                if c_id not in chunk_map:
                    chunk_map[c_id] = c.copy()
                    chunk_map[c_id]["fused_score"] = 0.0
                    chunk_map[c_id]["match_reasons"] = []
                
                rank = c.get(rank_key)
                if rank:
                    score = 1.0 / (self.rrf_k + rank)
                    chunk_map[c_id]["fused_score"] += score
                    if rank_key == "semantic_rank":
                        chunk_map[c_id]["match_reasons"].append(f"semantic rank {rank}")
                        chunk_map[c_id]["semantic_rank"] = rank
                    else:
                        chunk_map[c_id]["match_reasons"].append(f"lexical rank {rank}")
                        chunk_map[c_id]["lexical_rank"] = rank

        _add_to_map(semantic, "semantic_rank")
        _add_to_map(lexical, "lexical_rank")
        
        fused = list(chunk_map.values())
        fused.sort(key=lambda x: x["fused_score"], reverse=True)
        return fused

    def _apply_diversity(self, results: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """Basic deduplication: drop immediate neighbors if we have enough diverse results."""
        diverse = []
        seen_docs = set()
        last_chunk_index_by_doc = {}
        
        for r in results:
            doc_id = r["document_id"]
            c_index = r["chunk_index"]
            
            # Simple heuristic: if we just added chunk N from this doc, skip chunk N+1 or N-1 to force diversity
            # But only skip if we already have 2 chunks from this doc
            if doc_id in seen_docs:
                last_idx = last_chunk_index_by_doc[doc_id]
                if abs(c_index - last_idx) <= 1:
                    # It's an adjacent chunk, skip it for diversity
                    continue
            
            seen_docs.add(doc_id)
            last_chunk_index_by_doc[doc_id] = c_index
            diverse.append(r)
            
            if len(diverse) >= top_k:
                break
                
        # If we couldn't fill top_k due to diversity filtering, fallback to original top_k
        if len(diverse) < top_k and len(results) > len(diverse):
            # just take the top K of original
            return results[:top_k]
            
        return diverse
