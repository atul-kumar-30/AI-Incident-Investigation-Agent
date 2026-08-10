import enum
import uuid
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Integer, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, backref
from app.db.session import Base

class InvestigationRunStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class StepType(str, enum.Enum):
    PLANNING = "PLANNING"
    TOOL_CALL = "TOOL_CALL"
    TOOL_RESULT = "TOOL_RESULT"
    SYSTEM = "SYSTEM"

class StepStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class EvidenceSourceType(str, enum.Enum):
    LOG = "LOG"
    METRIC = "METRIC"
    TRACE = "TRACE"
    CODE = "CODE"
    GIT_CHANGE = "GIT_CHANGE"
    DOCUMENT = "DOCUMENT"
    USER = "USER"
    SYSTEM = "SYSTEM"
    TOOL = "TOOL"

class InvestigationRun(Base):
    __tablename__ = "investigation_runs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(InvestigationRunStatus), default=InvestigationRunStatus.PENDING, nullable=False)
    current_step = Column(String, nullable=True)
    summary = Column(String, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    incident = relationship("Incident", backref=backref("investigations", cascade="all, delete-orphan"))
    steps = relationship("InvestigationStep", backref="investigation_run", cascade="all, delete-orphan")
    evidence = relationship("Evidence", backref="investigation_run", cascade="all, delete-orphan")

class InvestigationStep(Base):
    __tablename__ = "investigation_steps"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_run_id = Column(String, ForeignKey("investigation_runs.id", ondelete="CASCADE"), nullable=False)
    step_number = Column(Integer, nullable=False)
    node_name = Column(String, nullable=False)
    step_type = Column(Enum(StepType), nullable=False)
    status = Column(Enum(StepStatus), default=StepStatus.PENDING, nullable=False)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_run_id = Column(String, ForeignKey("investigation_runs.id", ondelete="CASCADE"), nullable=False)
    source_type = Column(Enum(EvidenceSourceType), nullable=False)
    source_name = Column(String, nullable=False)
    content = Column(String, nullable=False)
    metadata_ = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
