from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from typing import List, Optional
from app.models.incident import Incident
from app.schemas.incident import IncidentCreate, IncidentUpdate

class IncidentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, incident_in: IncidentCreate) -> Incident:
        db_incident = Incident(
            title=incident_in.title,
            description=incident_in.description,
            severity=incident_in.severity,
            source=incident_in.source
        )
        self.session.add(db_incident)
        await self.session.commit()
        await self.session.refresh(db_incident)
        return db_incident

    async def get(self, incident_id: str) -> Optional[Incident]:
        result = await self.session.execute(select(Incident).where(Incident.id == incident_id))
        return result.scalars().first()

    async def get_multi(self, skip: int = 0, limit: int = 100) -> List[Incident]:
        result = await self.session.execute(
            select(Incident).order_by(desc(Incident.created_at)).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def update(self, db_incident: Incident, incident_in: IncidentUpdate) -> Incident:
        update_data = incident_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_incident, field, value)
            
        self.session.add(db_incident)
        await self.session.commit()
        await self.session.refresh(db_incident)
        return db_incident

    async def delete(self, db_incident: Incident) -> None:
        await self.session.delete(db_incident)
        await self.session.commit()
