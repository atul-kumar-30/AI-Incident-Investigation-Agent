from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.incident import IncidentStatus, IncidentSeverity, IncidentSource

class IncidentBase(BaseModel):
    title: str
    description: str
    severity: IncidentSeverity = IncidentSeverity.MEDIUM

class IncidentCreate(IncidentBase):
    source: IncidentSource = IncidentSource.API

class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[IncidentStatus] = None
    severity: Optional[IncidentSeverity] = None

class IncidentResponse(IncidentBase):
    id: str
    status: IncidentStatus
    source: IncidentSource
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
