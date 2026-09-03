import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.document import Document, DocumentType, DocumentStatus, DocumentSourceType
from app.models.incident import Incident, incident_documents
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])
logger = logging.getLogger(__name__)

document_service = DocumentService()

@router.post("")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_type: str = Form("GENERAL"),
    db: AsyncSession = Depends(get_db)
):
    try:
        doc_type = DocumentType(document_type.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document type")

    # Read content
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    doc = Document(
        title=file.filename or "Untitled Document",
        document_type=doc_type,
        source_type=DocumentSourceType.UPLOAD,
        source_name=file.filename or "upload",
        ingestion_status=DocumentStatus.PENDING
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    background_tasks.add_task(
        document_service.process_document,
        db=db,
        document_id=doc.id,
        file_name=doc.source_name,
        file_content=content,
        mime_type=file.content_type or ""
    )

    return {"id": doc.id, "title": doc.title, "status": doc.ingestion_status}

@router.get("")
async def list_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).order_by(Document.created_at.desc()))
    docs = result.scalars().all()
    return [{"id": d.id, "title": d.title, "type": d.document_type, "status": d.ingestion_status, "created_at": d.created_at} for d in docs]

@router.get("/{document_id}")
async def get_document(document_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Document).options(selectinload(Document.chunks)).filter_by(id=document_id)
    )
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    sorted_chunks = sorted(doc.chunks, key=lambda c: c.chunk_index)
    return {
        "id": doc.id,
        "title": doc.title,
        "type": doc.document_type,
        "status": doc.ingestion_status,
        "created_at": doc.created_at,
        "chunks": [
            {
                "id": c.id,
                "chunk_index": c.chunk_index,
                "section_title": c.section_title,
                "content": c.content,
                "page_number": c.page_number
            }
            for c in sorted_chunks
        ]
    }

@router.post("/demo")
async def ingest_demo_documents(db: AsyncSession = Depends(get_db)):
    """Seed database with canonical demo runbooks for Phase 5."""
    await document_service.ingest_demo_documents(db)
    return {"status": "ok"}

