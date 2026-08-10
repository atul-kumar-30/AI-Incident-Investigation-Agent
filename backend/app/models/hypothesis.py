import enum
import uuid
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Integer, JSON, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship as orm_relationship, backref
from app.db.session import Base

class HypothesisCategory(str, enum.Enum):
    APPLICATION = "APPLICATION"
    DATABASE = "DATABASE"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    CONFIGURATION = "CONFIGURATION"
    DEPLOYMENT = "DEPLOYMENT"
    DEPENDENCY = "DEPENDENCY"
    TRAFFIC = "TRAFFIC"
    AUTHENTICATION = "AUTHENTICATION"
    UNKNOWN = "UNKNOWN"

class HypothesisStatus(str, enum.Enum):
    PROPOSED = "PROPOSED"
    UNDER_REVIEW = "UNDER_REVIEW"
    SUPPORTED = "SUPPORTED"
    WEAKENED = "WEAKENED"
    INCONCLUSIVE = "INCONCLUSIVE"

class EvidenceRelationshipType(str, enum.Enum):
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    NEUTRAL = "NEUTRAL"
    CONTEXT = "CONTEXT"

class EvidenceStrength(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class EvidenceOrigin(str, enum.Enum):
    INITIAL = "INITIAL"
    VERIFICATION = "VERIFICATION"

class HypothesisVerificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class VerificationStepType(str, enum.Enum):
    PLANNING = "PLANNING"
    TOOL_CALL = "TOOL_CALL"
    TOOL_RESULT = "TOOL_RESULT"
    EVIDENCE_EVALUATION = "EVIDENCE_EVALUATION"
    SYSTEM = "SYSTEM"

class Hypothesis(Base):
    __tablename__ = "hypotheses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_run_id = Column(String, ForeignKey("investigation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    category = Column(Enum(HypothesisCategory), nullable=False)
    status = Column(Enum(HypothesisStatus), default=HypothesisStatus.PROPOSED, nullable=False, index=True)
    
    rank = Column(Integer, nullable=True, index=True)
    score = Column(Float, nullable=True)
    
    generation_source = Column(String, nullable=True) # e.g. "LLM", "USER"
    reasoning_summary = Column(String, nullable=True)
    
    missing_evidence = Column(JSON, nullable=True)
    verification_requirements = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    investigation_run = orm_relationship("InvestigationRun", backref=backref("hypotheses", cascade="all, delete-orphan"))

class HypothesisEvidence(Base):
    __tablename__ = "hypothesis_evidence"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    hypothesis_id = Column(String, ForeignKey("hypotheses.id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_id = Column(String, ForeignKey("evidence.id", ondelete="CASCADE"), nullable=False, index=True)
    verification_id = Column(String, ForeignKey("hypothesis_verifications.id", ondelete="CASCADE"), nullable=True, index=True)
    origin = Column(Enum(EvidenceOrigin), default=EvidenceOrigin.INITIAL, nullable=False)
    
    relationship = Column(Enum(EvidenceRelationshipType), nullable=False, index=True)
    strength = Column(Enum(EvidenceStrength), nullable=False)
    reason = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    hypothesis = orm_relationship("Hypothesis", backref=backref("evidence_mappings", cascade="all, delete-orphan"))
    evidence = orm_relationship("Evidence", backref=backref("hypothesis_mappings", cascade="all, delete-orphan"))

class HypothesisVerification(Base):
    __tablename__ = "hypothesis_verifications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    hypothesis_id = Column(String, ForeignKey("hypotheses.id", ondelete="CASCADE"), nullable=False, index=True)
    investigation_run_id = Column(String, ForeignKey("investigation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    status = Column(Enum(HypothesisVerificationStatus), default=HypothesisVerificationStatus.PENDING, nullable=False, index=True)
    verification_objective = Column(String, nullable=True)
    
    initial_score = Column(Float, nullable=True)
    final_score = Column(Float, nullable=True)
    
    support_delta = Column(Float, default=0.0)
    contradiction_delta = Column(Float, default=0.0)
    
    summary = Column(String, nullable=True)
    
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    hypothesis = orm_relationship("Hypothesis", backref=backref("verifications", cascade="all, delete-orphan"))
    investigation_run = orm_relationship("InvestigationRun", backref=backref("verifications", cascade="all, delete-orphan"))
    
class VerificationStep(Base):
    __tablename__ = "verification_steps"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    verification_id = Column(String, ForeignKey("hypothesis_verifications.id", ondelete="CASCADE"), nullable=False, index=True)
    step_number = Column(Integer, nullable=False, index=True)
    
    step_type = Column(Enum(VerificationStepType), nullable=False)
    status = Column(String, nullable=False)
    
    tool_name = Column(String, nullable=True)
    objective = Column(String, nullable=True)
    
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    verification = orm_relationship("HypothesisVerification", backref=backref("steps", cascade="all, delete-orphan"))
