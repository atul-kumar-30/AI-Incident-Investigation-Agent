from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Tuple
from datetime import datetime
from app.models.log import LogEntry
from app.schemas.log import LogEntryCreate
from app.repositories.log_repository import LogRepository
from fastapi import HTTPException
from app.services.incident_service import IncidentService

class LogService:
    def __init__(self, session: AsyncSession):
        self.repository = LogRepository(session)
        self.session = session

    async def bulk_ingest(self, incident_id: str, logs: List[LogEntryCreate]) -> List[LogEntry]:
        # Validate incident exists
        incident_service = IncidentService(self.session)
        await incident_service.get_incident(incident_id) # Raises 404 if not found
        
        # Max batch limit
        if len(logs) > 500:
            raise HTTPException(status_code=400, detail="Maximum batch size is 500 logs")
            
        return await self.repository.bulk_insert(incident_id, logs)

    async def search_logs(
        self,
        incident_id: str,
        query: Optional[str] = None,
        levels: Optional[List[str]] = None,
        services: Optional[List[str]] = None,
        endpoint: Optional[str] = None,
        http_status: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 25,
        offset: int = 0
    ) -> Tuple[int, List[LogEntry]]:
        
        # Validate incident exists
        incident_service = IncidentService(self.session)
        await incident_service.get_incident(incident_id) # Raises 404 if not found
        
        if limit > 100:
            limit = 100
            
        return await self.repository.search(
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
