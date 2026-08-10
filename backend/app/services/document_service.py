import hashlib
import json
import logging
import re
from typing import List, Dict, Any, Tuple, Optional
import fitz  # PyMuPDF
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.document import Document, DocumentChunk, DocumentStatus, DocumentType, DocumentSourceType
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class DocumentChunkInfo:
    def __init__(self, content: str, section_title: Optional[str] = None, page_number: Optional[int] = None, start_offset: Optional[int] = None, end_offset: Optional[int] = None):
        self.content = content.strip()
        self.section_title = section_title
        self.page_number = page_number
        self.start_offset = start_offset
        self.end_offset = end_offset

class DocumentService:
    def __init__(self):
        self.embedding_service = EmbeddingService()

    def _generate_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def extract_text_from_pdf(self, file_content: bytes) -> List[DocumentChunkInfo]:
        """Extracts text page-by-page from PDF, respecting pages."""
        chunks = []
        try:
            # fitz.open(stream=..., filetype="pdf")
            doc = fitz.open(stream=file_content, filetype="pdf")
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text("text")
                if text and text.strip():
                    # We can further chunk the page if it's too large, but for now, page-level is a good start.
                    # Let's chunk the page text if it exceeds 2000 chars.
                    page_chunks = self._chunk_text(text, max_chars=2000)
                    for pc in page_chunks:
                        pc.page_number = page_num + 1
                        chunks.append(pc)
            doc.close()
        except Exception as e:
            logger.error(f"Error extracting PDF: {e}")
            raise ValueError(f"Failed to extract PDF text: {e}")
            
        return chunks

    def extract_text_from_md(self, content: str) -> List[DocumentChunkInfo]:
        """Extracts text from markdown, respecting headers."""
        chunks = []
        lines = content.split('\n')
        current_section = "General"
        current_text = []
        
        for line in lines:
            header_match = re.match(r'^(#{1,6})\s+(.*)', line)
            if header_match:
                # If we have accumulated text, save it as a chunk
                if current_text:
                    section_text = "\n".join(current_text)
                    if section_text.strip():
                        sub_chunks = self._chunk_text(section_text, max_chars=2000)
                        for sc in sub_chunks:
                            sc.section_title = current_section
                            chunks.append(sc)
                current_section = header_match.group(2).strip()
                current_text = [line]
            else:
                current_text.append(line)
                
        if current_text:
            section_text = "\n".join(current_text)
            if section_text.strip():
                sub_chunks = self._chunk_text(section_text, max_chars=2000)
                for sc in sub_chunks:
                    sc.section_title = current_section
                    chunks.append(sc)
                    
        return chunks

    def extract_text_from_txt(self, content: str) -> List[DocumentChunkInfo]:
        """Extracts text from plain text."""
        return self._chunk_text(content, max_chars=2000)

    def _chunk_text(self, text: str, max_chars: int = 2000, overlap: int = 200) -> List[DocumentChunkInfo]:
        """Basic text chunker with overlap on paragraph/newline boundaries."""
        chunks = []
        if not text:
            return chunks
            
        # Split by double newline (paragraphs)
        paragraphs = re.split(r'\n\s*\n', text)
        
        current_chunk_text = ""
        for p in paragraphs:
            if not p.strip():
                continue
                
            if len(current_chunk_text) + len(p) < max_chars:
                current_chunk_text += p + "\n\n"
            else:
                if current_chunk_text.strip():
                    chunks.append(DocumentChunkInfo(content=current_chunk_text))
                
                # If a single paragraph is larger than max_chars, we just add it (or could split by sentences).
                # For simplicity, if it's too big, just start a new chunk with it.
                current_chunk_text = p + "\n\n"
                
        if current_chunk_text.strip():
            chunks.append(DocumentChunkInfo(content=current_chunk_text))
            
        return chunks

    async def process_document(self, db: AsyncSession, document_id: str, file_name: str, file_content: bytes, mime_type: str):
        """Background task to extract, chunk, and embed a document."""
        # 1. Fetch document
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()
        
        if not document:
            logger.error(f"Document {document_id} not found.")
            return

        document.ingestion_status = DocumentStatus.PROCESSING
        await db.commit()
        
        try:
            # 2. Extract and Chunk
            raw_text_content = ""
            if mime_type == "application/pdf" or file_name.endswith(".pdf"):
                chunks_info = self.extract_text_from_pdf(file_content)
                raw_text_content = "\n".join([c.content for c in chunks_info])
            elif mime_type == "text/markdown" or file_name.endswith(".md"):
                text = file_content.decode('utf-8')
                raw_text_content = text
                chunks_info = self.extract_text_from_md(text)
            else:
                text = file_content.decode('utf-8')
                raw_text_content = text
                chunks_info = self.extract_text_from_txt(text)

            content_hash = self._generate_hash(raw_text_content)

            # Deduplication: if content hash hasn't changed, we can skip if already READY (handled by caller typically)
            # But here we are processing, so we'll just clear old chunks and insert new ones
            
            # Clean old chunks if any
            await db.execute(DocumentChunk.__table__.delete().where(DocumentChunk.document_id == document_id))
            
            if not chunks_info:
                raise ValueError("No text could be extracted from document.")

            # 3. Embed
            texts_to_embed = [c.content for c in chunks_info]
            embeddings = await self.embedding_service.embed_documents(texts_to_embed)

            # 4. Save Chunks
            for i, (info, emb) in enumerate(zip(chunks_info, embeddings)):
                chunk_hash = self._generate_hash(info.content)
                chunk = DocumentChunk(
                    document_id=document_id,
                    chunk_index=i,
                    section_title=info.section_title,
                    page_number=info.page_number,
                    content=info.content,
                    content_hash=chunk_hash,
                    embedding=emb
                )
                db.add(chunk)
                
            document.content_hash = content_hash
            document.ingestion_status = DocumentStatus.READY
            await db.commit()
            
        except Exception as e:
            logger.error(f"Failed to process document {document_id}: {e}")
            document.ingestion_status = DocumentStatus.FAILED
            await db.commit()
            raise

    async def ingest_demo_documents(self, db: AsyncSession):
        """Seeds the database with canonical demo runbooks for Phase 5 tests."""
        demo_docs = [
            {
                "title": "Database Connection Pool Exhaustion",
                "type": DocumentType.RUNBOOK,
                "filename": "db_pool_exhaustion.md",
                "content": """# Database Connection Pool Exhaustion

## Symptoms
- connection acquisition timeouts
- HTTP 5xx from dependent services
- active connections at configured pool limit

## Common Causes
- Spikes in application traffic
- Long-running queries holding connections
- Reduced pool_size configuration during recent deployments

## Validation Steps
- compare active connection count against pool_size
- inspect DB max_connections
- correlate failure timing with configuration changes or deployments

## Mitigation
- Increase pool_size if DB has capacity
- Kill long-running idle transactions
- Rollback recent config changes if they reduced capacity
"""
            },
            {
                "title": "Authentication Service HTTP 5xx Troubleshooting",
                "type": DocumentType.TROUBLESHOOTING,
                "filename": "auth_5xx.md",
                "content": """# Authentication Service HTTP 5xx Troubleshooting

## Overview
When the Authentication Service returns 500 errors, it usually indicates a failure to communicate with its backend dependencies.

## Symptoms
- HTTP 500 or 502 returned on /login endpoints
- Users unable to authenticate

## Validation
- Check Authentication Service logs for specific timeout or connection errors
- Verify Database health and connection pool metrics
- Verify Redis caching layer health
"""
            },
            {
                "title": "Authentication Service Architecture",
                "type": DocumentType.ARCHITECTURE,
                "filename": "auth_architecture.md",
                "content": """# Authentication Service Architecture

The Auth service provides JWT token generation and validation.
It connects to a PostgreSQL database for user credentials and Redis for session revocation.
The database connection pool is configured via environment variables, typically pool_size=50.
"""
            },
            {
                "title": "Email Notification Retries",
                "type": DocumentType.GENERAL,
                "filename": "email_noise.md",
                "content": """# Email Notification Retries

If emails fail to send, the worker will retry up to 5 times using exponential backoff.
This is unrelated to database timeouts or authentication.
"""
            }
        ]

        for doc_data in demo_docs:
            content_hash = self._generate_hash(doc_data["content"])
            
            # Check if exists
            result = await db.execute(select(Document).where(Document.title == doc_data["title"]))
            existing = result.scalar_one_or_none()
            if existing and existing.content_hash == content_hash and existing.ingestion_status == DocumentStatus.READY:
                continue
                
            if existing:
                doc = existing
                doc.ingestion_status = DocumentStatus.PENDING
            else:
                doc = Document(
                    title=doc_data["title"],
                    document_type=doc_data["type"],
                    source_type=DocumentSourceType.GENERATED_DEMO,
                    source_name=doc_data["filename"]
                )
                db.add(doc)
            
            await db.commit()
            
            # Process synchronously for demo data
            await self.process_document(db, doc.id, doc_data["filename"], doc_data["content"].encode('utf-8'), "text/markdown")
