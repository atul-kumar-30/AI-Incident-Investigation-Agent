from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Integer, JSON
from sqlalchemy.sql import func
import enum
import uuid
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship

from app.db.session import Base

class DocumentType(str, enum.Enum):
    RUNBOOK = "RUNBOOK"
    ARCHITECTURE = "ARCHITECTURE"
    SERVICE_DOC = "SERVICE_DOC"
    TROUBLESHOOTING = "TROUBLESHOOTING"
    POSTMORTEM = "POSTMORTEM"
    GENERAL = "GENERAL"

class DocumentSourceType(str, enum.Enum):
    UPLOAD = "UPLOAD"
    LOCAL = "LOCAL"
    GENERATED_DEMO = "GENERATED_DEMO"

class DocumentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    document_type = Column(Enum(DocumentType), default=DocumentType.GENERAL, nullable=False)
    source_type = Column(Enum(DocumentSourceType), default=DocumentSourceType.UPLOAD, nullable=False)
    source_name = Column(String, nullable=False)
    content_hash = Column(String, nullable=True)
    ingestion_status = Column(Enum(DocumentStatus), default=DocumentStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    section_title = Column(String, nullable=True)
    page_number = Column(Integer, nullable=True)
    start_offset = Column(Integer, nullable=True)
    end_offset = Column(Integer, nullable=True)
    content = Column(String, nullable=False)
    content_hash = Column(String, nullable=False)
    # The dimension must match EMBEDDING_DIMENSION (768).
    embedding = Column(Vector(768), nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    document = relationship("Document", back_populates="chunks")
