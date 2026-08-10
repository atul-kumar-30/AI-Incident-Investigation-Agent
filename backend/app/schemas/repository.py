from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.repository import RepositorySourceType, IngestionStatus

class RepositoryCreate(BaseModel):
    name: str
    source_type: RepositorySourceType = RepositorySourceType.LOCAL
    source_location: str
    default_branch: Optional[str] = None

class RepositoryResponse(BaseModel):
    id: str
    name: str
    source_type: RepositorySourceType
    source_location: str
    default_branch: Optional[str] = None
    current_commit: Optional[str] = None
    ingestion_status: IngestionStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SourceFileResponse(BaseModel):
    id: str
    repository_id: str
    path: str
    language: Optional[str]
    size_bytes: Optional[int]
    content_hash: Optional[str]
    indexed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class CodeChunkResponse(BaseModel):
    id: str
    source_file_id: str
    start_line: int
    end_line: int
    symbol_name: Optional[str]
    chunk_type: Optional[str]
    content: str
    content_hash: str

    model_config = ConfigDict(from_attributes=True)
