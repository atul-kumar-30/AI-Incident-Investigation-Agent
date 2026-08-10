import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from app.models.repository import Repository, IngestionStatus
from app.models.incident import incident_repositories
from app.schemas.repository import RepositoryCreate
from app.core.config import settings

class RepositoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _validate_path(self, target_path: str):
        # Resolve to absolute path
        abs_target = os.path.abspath(target_path)
        allowed_root = os.path.abspath(settings.REPOSITORY_ALLOWED_ROOT)
        
        if not abs_target.startswith(allowed_root):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Repository path is outside the allowed root directory."
            )
            
        if not os.path.exists(abs_target):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Repository path does not exist: {abs_target}"
            )
            
        if not os.path.isdir(abs_target):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Repository path must be a directory."
            )

    async def create_repository(self, repo_in: RepositoryCreate) -> Repository:
        self._validate_path(repo_in.source_location)
        
        # Check if already exists
        result = await self.db.execute(
            select(Repository).filter_by(source_location=repo_in.source_location)
        )
        existing = result.scalars().first()
        if existing:
            return existing

        repo = Repository(
            name=repo_in.name,
            source_type=repo_in.source_type,
            source_location=repo_in.source_location,
            default_branch=repo_in.default_branch,
            ingestion_status=IngestionStatus.PENDING
        )
        self.db.add(repo)
        await self.db.commit()
        await self.db.refresh(repo)
        return repo

    async def get_repositories(self) -> list[Repository]:
        result = await self.db.execute(select(Repository))
        return list(result.scalars().all())

    async def get_repository(self, repo_id: str) -> Repository:
        result = await self.db.execute(select(Repository).filter_by(id=repo_id))
        repo = result.scalars().first()
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")
        return repo

    async def associate_incident(self, incident_id: str, repo_id: str):
        # Check if already associated
        result = await self.db.execute(
            select(incident_repositories).where(
                (incident_repositories.c.incident_id == incident_id) &
                (incident_repositories.c.repository_id == repo_id)
            )
        )
        if result.first():
            return
            
        await self.db.execute(
            incident_repositories.insert().values(
                incident_id=incident_id, 
                repository_id=repo_id
            )
        )
        await self.db.commit()
