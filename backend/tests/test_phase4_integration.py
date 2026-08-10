import pytest
import os
import subprocess
from app.models.investigation import InvestigationRunStatus
from app.services.repository_service import RepositoryService
from app.services.indexer import IndexerService
from app.models.incident import Incident
from app.schemas.repository import RepositoryCreate, RepositorySourceType

@pytest.fixture
def demo_git_repo(tmp_path):
    repo_dir = tmp_path / "demo_git_repo"
    repo_dir.mkdir()
    
    # Initialize git
    subprocess.run(["git", "init"], cwd=str(repo_dir), check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=str(repo_dir), check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(repo_dir), check=True)
    
    # Create files
    main_py = repo_dir / "main.py"
    main_py.write_text("def connect_db():\n    # Establish database connection\n    pool = create_pool(timeout=30)\n    return pool\n")
    
    auth_ts = repo_dir / "auth.ts"
    auth_ts.write_text("export function login() {\n  return true;\n}\n")
    
    # Commit
    subprocess.run(["git", "add", "."], cwd=str(repo_dir), check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit: add db pool and auth"], cwd=str(repo_dir), check=True)
    
    # Modify file to create a recent change
    main_py.write_text("def connect_db():\n    # Establish database connection\n    pool = create_pool(timeout=5) # Reduced timeout!\n    return pool\n")
    subprocess.run(["git", "add", "main.py"], cwd=str(repo_dir), check=True)
    subprocess.run(["git", "commit", "-m", "fix: reduce db pool timeout"], cwd=str(repo_dir), check=True)
    
    yield str(repo_dir)

@pytest.mark.asyncio
async def test_full_phase4_investigation_loop(db_session, demo_git_repo):
    from app.core.config import settings
    from app.services.investigation_service import InvestigationService
    from sqlalchemy.future import select
    from app.models.investigation import Evidence
    from app.agents.investigation.llm import FakeStructuredLLM
    
    FakeStructuredLLM.call_count = 0
    
    original_root = settings.REPOSITORY_ALLOWED_ROOT
    settings.REPOSITORY_ALLOWED_ROOT = demo_git_repo
    
    try:
        # 1. Create incident
        incident = Incident(
            title="Database timeouts during login",
            description="Users are reporting timeouts during login. Looks like a database connection pool issue."
        )
        db_session.add(incident)
        await db_session.commit()
        await db_session.refresh(incident)
        
        # 2. Register Repository
        repo_service = RepositoryService(db_session)
        indexer_service = IndexerService(db_session)
        
        repo_create = RepositoryCreate(
            name="backend-demo",
            source_type=RepositorySourceType.GIT,
            source_location=demo_git_repo
        )
        repo = await repo_service.create_repository(repo_create)
        
        # 3. Associate repository
        await repo_service.associate_incident(incident.id, repo.id)
        
        # 4. Index repository
        await indexer_service.index_repository(repo.id)
        
        # 5. Start Investigation (Using Mock LLM which iterates 5 times now)
        run = await InvestigationService.start_investigation(db_session, incident.id)
        
        # In a real async flow, the graph would run in background. 
        # But start_investigation in test environment (if synchronously dispatched) or we wait.
        # Wait for completion
        import asyncio
        for _ in range(20):
            await db_session.refresh(run)
            if run.status in (InvestigationRunStatus.COMPLETED, InvestigationRunStatus.FAILED):
                break
            await asyncio.sleep(0.5)
            
        assert run.status == InvestigationRunStatus.COMPLETED
        
        # 6. Verify Evidence Collected
        result = await db_session.execute(
            select(Evidence).where(Evidence.investigation_run_id == run.id)
        )
        evidence = result.scalars().all()
        
        source_types = [e.source_type for e in evidence]
        # We expect TOOL (context), LOG (log search 1), LOG (log search 2), CODE (code search), GIT_CHANGE (recent changes)
        assert "CODE" in source_types
        assert "GIT_CHANGE" in source_types
        
        # Verify the code search found the pool timeout
        code_evidence = next(e for e in evidence if e.source_type == "CODE")
        assert "def connect_db" in code_evidence.content
        assert "timeout=5" in code_evidence.content
        
        # Verify the git change found the commit
        git_evidence = next(e for e in evidence if e.source_type == "GIT_CHANGE")
        assert "reduce db pool timeout" in git_evidence.content
        
    finally:
        settings.REPOSITORY_ALLOWED_ROOT = original_root
