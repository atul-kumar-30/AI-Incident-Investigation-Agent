from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.models.log import LogLevel

class LogEntryBase(BaseModel):
    timestamp: datetime
    level: LogLevel
    service: str
    environment: Optional[str] = None
    message: str
    trace_id: Optional[str] = None
    request_id: Optional[str] = None
    endpoint: Optional[str] = None
    http_status: Optional[int] = None
    metadata_: Optional[Dict[str, Any]] = None

class LogEntryCreate(LogEntryBase):
    pass

class LogEntryResponse(LogEntryBase):
    id: str
    incident_id: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class LogBatchIngest(BaseModel):
    logs: List[LogEntryCreate]
