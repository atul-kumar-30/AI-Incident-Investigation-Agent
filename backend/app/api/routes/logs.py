from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
from app.db.session import get_db
from app.schemas.log import LogEntryResponse, LogBatchIngest
from app.services.log_service import LogService
from app.core.logging import logger

router = APIRouter()

def get_log_service(db: AsyncSession = Depends(get_db)) -> LogService:
    return LogService(db)

@router.post("/incidents/{incident_id}/logs", response_model=List[LogEntryResponse], status_code=status.HTTP_201_CREATED)
async def ingest_logs(
    incident_id: str,
    batch: LogBatchIngest,
    service: LogService = Depends(get_log_service)
):
    logger.info(f"Ingesting {len(batch.logs)} logs for incident {incident_id}")
    return await service.bulk_ingest(incident_id, batch.logs)

@router.get("/incidents/{incident_id}/logs", response_model=List[LogEntryResponse])
async def search_logs(
    incident_id: str,
    query: Optional[str] = None,
    levels: Optional[List[str]] = Query(None),
    services: Optional[List[str]] = Query(None),
    endpoint: Optional[str] = None,
    http_status: Optional[int] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: LogService = Depends(get_log_service)
):
    logger.info(f"Searching logs for incident {incident_id}")
    total_matches, logs = await service.search_logs(
        incident_id=incident_id,
        query=query,
        levels=levels,
        services=services,
        endpoint=endpoint,
        http_status=http_status,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset
    )
    # The API currently returns a list of logs, we could return a paginated response object later
    return logs
