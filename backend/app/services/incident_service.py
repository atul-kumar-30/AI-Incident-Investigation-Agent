from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from fastapi import HTTPException
from app.models.incident import Incident
from app.schemas.incident import IncidentCreate, IncidentUpdate
from app.repositories.incident_repository import IncidentRepository

class IncidentService:
    def __init__(self, session: AsyncSession):
        self.repository = IncidentRepository(session)

    async def create_incident(self, incident_in: IncidentCreate) -> Incident:
        return await self.repository.create(incident_in)

    async def get_incident(self, incident_id: str) -> Incident:
        incident = await self.repository.get(incident_id)
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        return incident

    async def get_incidents(self, skip: int = 0, limit: int = 100) -> List[Incident]:
        return await self.repository.get_multi(skip=skip, limit=limit)

    async def update_incident(self, incident_id: str, incident_in: IncidentUpdate) -> Incident:
        db_incident = await self.repository.get(incident_id)
        if not db_incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        return await self.repository.update(db_incident, incident_in)

    async def delete_incident(self, incident_id: str) -> None:
        db_incident = await self.repository.get(incident_id)
        if not db_incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        await self.repository.delete(db_incident)
