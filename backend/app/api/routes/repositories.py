from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_db
from app.schemas.repository import RepositoryCreate, RepositoryResponse
from app.services.repository_service import RepositoryService
from app.services.indexer import IndexerService
from app.core.logging import logger

router = APIRouter()

def get_repository_service(db: AsyncSession = Depends(get_db)) -> RepositoryService:
    return RepositoryService(db)

def get_indexer_service(db: AsyncSession = Depends(get_db)) -> IndexerService:
    return IndexerService(db)

@router.post("/repositories", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
async def create_repository(
    repo_in: RepositoryCreate,
    service: RepositoryService = Depends(get_repository_service)
):
    logger.info(f"Creating repository: {repo_in.name}")
    return await service.create_repository(repo_in)

@router.get("/repositories", response_model=List[RepositoryResponse])
async def list_repositories(
    service: RepositoryService = Depends(get_repository_service)
):
    logger.info("Listing repositories")
    return await service.get_repositories()

@router.get("/repositories/{repo_id}", response_model=RepositoryResponse)
async def get_repository(
    repo_id: str,
    service: RepositoryService = Depends(get_repository_service)
):
    return await service.get_repository(repo_id)

@router.post("/incidents/{incident_id}/repositories/{repo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def associate_repository(
    incident_id: str,
    repo_id: str,
    service: RepositoryService = Depends(get_repository_service)
):
    logger.info(f"Associating repository {repo_id} with incident {incident_id}")
    await service.associate_incident(incident_id, repo_id)

@router.post("/repositories/{repo_id}/index", status_code=status.HTTP_202_ACCEPTED)
async def index_repository(
    repo_id: str,
    background_tasks: BackgroundTasks,
    service: IndexerService = Depends(get_indexer_service)
):
    logger.info(f"Triggering indexing for repository {repo_id}")
    background_tasks.add_task(service.index_repository, repo_id)
    return {"message": "Indexing started in the background"}
