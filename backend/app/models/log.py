import enum
import uuid
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Integer, JSON
from sqlalchemy.sql import func
from app.db.session import Base

class LogLevel(str, enum.Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogEntry(Base):
    __tablename__ = "log_entries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    level = Column(Enum(LogLevel), nullable=False, index=True)
    service = Column(String, nullable=False, index=True)
    environment = Column(String, nullable=True)
    message = Column(String, nullable=False)
    trace_id = Column(String, nullable=True)
    request_id = Column(String, nullable=True)
    endpoint = Column(String, nullable=True, index=True)
    http_status = Column(Integer, nullable=True, index=True)
    metadata_ = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
