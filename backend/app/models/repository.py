import enum
import uuid
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Integer, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base

class RepositorySourceType(str, enum.Enum):
    LOCAL = "LOCAL"
    GIT = "GIT"

class IngestionStatus(str, enum.Enum):
    PENDING = "PENDING"
    INDEXING = "INDEXING"
    READY = "READY"
    FAILED = "FAILED"

class Repository(Base):
    __tablename__ = "repositories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    source_type = Column(Enum(RepositorySourceType), nullable=False)
    source_location = Column(String, nullable=False)
    default_branch = Column(String, nullable=True)
    current_commit = Column(String, nullable=True)
    ingestion_status = Column(Enum(IngestionStatus), default=IngestionStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    source_files = relationship("SourceFile", backref="repository", cascade="all, delete-orphan")


class SourceFile(Base):
    __tablename__ = "source_files"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    path = Column(String, nullable=False, index=True)
    language = Column(String, nullable=True)
    size_bytes = Column(BigInteger, nullable=True)
    content_hash = Column(String, nullable=True)
    indexed_at = Column(DateTime(timezone=True), nullable=True)

    chunks = relationship("CodeChunk", backref="source_file", cascade="all, delete-orphan")


class CodeChunk(Base):
    __tablename__ = "code_chunks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_file_id = Column(String, ForeignKey("source_files.id", ondelete="CASCADE"), nullable=False)
    start_line = Column(Integer, nullable=False)
    end_line = Column(Integer, nullable=False)
    symbol_name = Column(String, nullable=True, index=True)
    chunk_type = Column(String, nullable=True)
    content = Column(String, nullable=False)
    content_hash = Column(String, nullable=False)
