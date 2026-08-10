import pytest
import os
import shutil
from typing import AsyncGenerator
from httpx import AsyncClient
from app.models.investigation import InvestigationRunStatus
from app.models.incident import Incident
from app.models.repository import Repository, SourceFile, CodeChunk, RepositorySourceType
from app.services.repository_service import RepositoryService
from app.services.indexer import IndexerService

@pytest.fixture
def mock_repo_dir(tmp_path):
    repo_dir = tmp_path / "mock_repo"
    repo_dir.mkdir()
    
    # Create some mock source code
    main_py = repo_dir / "main.py"
    main_py.write_text("def hello():\n    print('world')\n")
    
    auth_ts = repo_dir / "auth.ts"
    auth_ts.write_text("export function login() {\n  return true;\n}\n")
    
    yield str(repo_dir)

@pytest.mark.asyncio
async def test_repository_indexing(db_session, mock_repo_dir):
    # Set the allowed root temporarily to our temp path
    from app.core.config import settings
    original_root = settings.REPOSITORY_ALLOWED_ROOT
    settings.REPOSITORY_ALLOWED_ROOT = mock_repo_dir
    
    try:
        repo_service = RepositoryService(db_session)
        indexer_service = IndexerService(db_session)
        
        # 1. Create a Repository
        from app.schemas.repository import RepositoryCreate
        repo_create = RepositoryCreate(
            name="test_repo",
            source_type=RepositorySourceType.LOCAL,
            source_location=mock_repo_dir
        )
        repo = await repo_service.create_repository(repo_create)
        assert repo.id is not None
        
        # 2. Index the repository
        await indexer_service.index_repository(repo.id)
        
        # 3. Verify indexed files
        from sqlalchemy.future import select
        result = await db_session.execute(select(SourceFile).where(SourceFile.repository_id == repo.id))
        files = result.scalars().all()
        assert len(files) == 2
        paths = [f.path for f in files]
        assert "main.py" in paths
        assert "auth.ts" in paths
        
        # 4. Verify chunks
        result = await db_session.execute(select(CodeChunk).where(CodeChunk.source_file_id == files[0].id))
        chunks = result.scalars().all()
        assert len(chunks) == 1
        
    finally:
        settings.REPOSITORY_ALLOWED_ROOT = original_root

@pytest.mark.asyncio
async def test_code_search_tool(db_session, mock_repo_dir):
    from app.core.config import settings
    original_root = settings.REPOSITORY_ALLOWED_ROOT
    settings.REPOSITORY_ALLOWED_ROOT = mock_repo_dir
    
    try:
        repo_service = RepositoryService(db_session)
        indexer_service = IndexerService(db_session)
        
        from app.schemas.repository import RepositoryCreate
        repo_create = RepositoryCreate(
            name="test_repo_2",
            source_type=RepositorySourceType.LOCAL,
            source_location=mock_repo_dir
        )
        repo = await repo_service.create_repository(repo_create)
        await indexer_service.index_repository(repo.id)
        
        # Create incident
        incident = Incident(title="Test", description="Test")
        db_session.add(incident)
        await db_session.commit()
        await db_session.refresh(incident)
        
        # Associate repo
        await repo_service.associate_incident(incident.id, repo.id)
        
        # Search
        from app.agents.investigation.tools.code_search import CodeSearchTool
        
        tool = CodeSearchTool()
        
        result = await tool.execute(
            incident_id=incident.id,
            repository_ids=[repo.id],
            query="hello",
            limit=10
        )
        
        assert result["total_matches"] == 1
        assert result["results"][0]["file_path"] == "main.py"
        assert result["results"][0]["symbol_name"] == "hello"
        
    finally:
        settings.REPOSITORY_ALLOWED_ROOT = original_root
