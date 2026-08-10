import enum
from sqlalchemy import Column, String, DateTime, Enum, Table, ForeignKey
from sqlalchemy.sql import func
import uuid
from sqlalchemy.orm import relationship
from app.db.session import Base

incident_repositories = Table(
    "incident_repositories",
    Base.metadata,
    Column("incident_id", String, ForeignKey("incidents.id", ondelete="CASCADE"), primary_key=True),
    Column("repository_id", String, ForeignKey("repositories.id", ondelete="CASCADE"), primary_key=True),
)

incident_documents = Table(
    "incident_documents",
    Base.metadata,
    Column("incident_id", String, ForeignKey("incidents.id", ondelete="CASCADE"), primary_key=True),
    Column("document_id", String, ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True),
)

class IncidentStatus(str, enum.Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    FAILED = "FAILED"

class IncidentSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class IncidentSource(str, enum.Enum):
    MANUAL = "MANUAL"
    API = "API"

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    status = Column(Enum(IncidentStatus), default=IncidentStatus.OPEN, nullable=False)
    severity = Column(Enum(IncidentSeverity), default=IncidentSeverity.MEDIUM, nullable=False)
    source = Column(Enum(IncidentSource), default=IncidentSource.API, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    repositories = relationship("Repository", secondary=incident_repositories, backref="incidents")
    documents = relationship("Document", secondary=incident_documents, backref="incidents")
