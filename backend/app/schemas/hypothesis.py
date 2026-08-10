from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from app.models.hypothesis import HypothesisCategory, HypothesisStatus, EvidenceRelationshipType, EvidenceStrength
from app.schemas.investigation import EvidenceResponse

class HypothesisEvidenceResponse(BaseModel):
    id: str
    hypothesis_id: str
    evidence_id: str
    relationship: EvidenceRelationshipType
    strength: EvidenceStrength
    reason: Optional[str]
    created_at: datetime
    
    # Nested evidence content
    evidence: Optional[EvidenceResponse] = None

    class Config:
        from_attributes = True

class HypothesisResponse(BaseModel):
    id: str
    investigation_run_id: str
    title: str
    description: str
    category: HypothesisCategory
    status: HypothesisStatus
    rank: Optional[int]
    score: Optional[float] = None
    generation_source: Optional[str]
    reasoning_summary: Optional[str]
    missing_evidence: Optional[List[Dict[str, Any]]]
    verification_requirements: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    
    # We can include counts or the actual evidence
    evidence_mappings: Optional[List[HypothesisEvidenceResponse]] = []
    
    class Config:
        from_attributes = True
