from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from sqlalchemy.future import select
from app.db.session import get_db
from app.schemas.incident import IncidentCreate, IncidentUpdate, IncidentResponse
from app.services.incident_service import IncidentService
from app.models.incident import incident_documents
from app.core.logging import logger

router = APIRouter()

def get_incident_service(db: AsyncSession = Depends(get_db)) -> IncidentService:
    return IncidentService(db)

@router.post("", response_model=IncidentResponse, status_code=201)
async def create_incident(
    incident_in: IncidentCreate,
    service: IncidentService = Depends(get_incident_service)
):
    logger.info(f"Creating incident: {incident_in.title}")
    return await service.create_incident(incident_in)

@router.get("", response_model=List[IncidentResponse])
async def list_incidents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    service: IncidentService = Depends(get_incident_service)
):
    logger.info(f"Listing incidents skip={skip} limit={limit}")
    return await service.get_incidents(skip=skip, limit=limit)

@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: str,
    service: IncidentService = Depends(get_incident_service)
):
    logger.info(f"Fetching incident {incident_id}")
    return await service.get_incident(incident_id)

@router.patch("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: str,
    incident_in: IncidentUpdate,
    service: IncidentService = Depends(get_incident_service)
):
    logger.info(f"Updating incident {incident_id}")
    return await service.update_incident(incident_id, incident_in)

@router.delete("/{incident_id}", status_code=204)
async def delete_incident(
    incident_id: str,
    service: IncidentService = Depends(get_incident_service)
):
    logger.info(f"Deleting incident {incident_id}")
    await service.delete_incident(incident_id)

@router.post("/{incident_id}/documents/{document_id}")
async def assign_document(
    incident_id: str,
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    # Verify both exist (in a real app, handled by service)
    await db.execute(incident_documents.insert().values(incident_id=incident_id, document_id=document_id))
    await db.commit()
    return {"status": "ok"}
    
@router.get("/{incident_id}/documents")
async def list_incident_documents(
    incident_id: str,
    db: AsyncSession = Depends(get_db)
):
    from app.models.document import Document
    result = await db.execute(
        select(Document).join(incident_documents).where(incident_documents.c.incident_id == incident_id)
    )
    docs = result.scalars().all()
    return [{"id": d.id, "title": d.title, "type": d.document_type, "status": d.ingestion_status} for d in docs]
