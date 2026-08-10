from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.investigation import InvestigationRunStatus, StepType, StepStatus, EvidenceSourceType

class EvidenceBase(BaseModel):
    source_type: EvidenceSourceType
    source_name: str
    content: str
    metadata_: Optional[Dict[str, Any]] = None

class EvidenceResponse(EvidenceBase):
    id: str
    investigation_run_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class InvestigationStepBase(BaseModel):
    step_number: int
    node_name: str
    step_type: StepType
    status: StepStatus
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None

class InvestigationStepResponse(InvestigationStepBase):
    id: str
    investigation_run_id: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class InvestigationRunBase(BaseModel):
    incident_id: str

class InvestigationRunResponse(InvestigationRunBase):
    id: str
    status: InvestigationRunStatus
    current_step: Optional[str] = None
    summary: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
