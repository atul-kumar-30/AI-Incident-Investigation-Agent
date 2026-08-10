import os
import sys
import pytest
import pytest_asyncio
import subprocess
from testcontainers.postgres import PostgresContainer
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.future import select
import uuid
from datetime import datetime, timezone

from app.models.incident import Incident, IncidentSeverity, IncidentStatus
from app.models.hypothesis import (
    Hypothesis, HypothesisStatus, HypothesisEvidence, 
    EvidenceRelationshipType, EvidenceStrength,
    HypothesisVerification, VerificationStep, VerificationStepType,
    HypothesisCategory
)
from app.models.investigation import InvestigationRun, InvestigationRunStatus, Evidence, EvidenceSourceType

@pytest_asyncio.fixture(scope="module")
async def pg_engine():
    # Spin up testcontainer
    postgres = PostgresContainer("pgvector/pgvector:pg15")
    postgres.start()
    
    sync_url = postgres.get_connection_url()
    async_url = sync_url.replace("postgresql+psycopg2", "postgresql+asyncpg")
    
    env = os.environ.copy()
    env["DATABASE_URL"] = async_url
    
    # Run Alembic migrations using the venv Python (not system alembic which lacks pgvector)
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        capture_output=True, text=True, env=env
    )
    if result.returncode != 0:
        postgres.stop()
        raise Exception(f"Alembic migration failed: {result.stderr}\n{result.stdout}")
        
    engine = create_async_engine(async_url, echo=False)
    yield engine
    
    await engine.dispose()
    postgres.stop()

@pytest_asyncio.fixture
async def db_session(pg_engine):
    SessionLocal = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session

@pytest.mark.asyncio
async def test_postgres_integration_phase7(db_session: AsyncSession):
    # 1. Create base data
    incident = Incident(
        id=str(uuid.uuid4()),
        title="DB test",
        description="A test incident",
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.OPEN,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(incident)
    
    run = InvestigationRun(
        id=str(uuid.uuid4()),
        incident_id=incident.id,
        status=InvestigationRunStatus.RUNNING
    )
    db_session.add(run)
    await db_session.flush()

    # 2. Test Hypothesis insertion
    hypothesis = Hypothesis(
        id=str(uuid.uuid4()),
        investigation_run_id=run.id,
        title="Test Hypothesis",
        description="Verification test",
        category=HypothesisCategory.INFRASTRUCTURE,
        status=HypothesisStatus.PROPOSED,
        score=10.0,
        rank=1
    )
    db_session.add(hypothesis)
    await db_session.flush()

    # 3. Test HypothesisVerification and VerificationStep tables
    verification = HypothesisVerification(
        id=str(uuid.uuid4()),
        hypothesis_id=hypothesis.id,
        investigation_run_id=run.id,
        status="RUNNING"
    )
    db_session.add(verification)
    await db_session.flush()

    step = VerificationStep(
        id=str(uuid.uuid4()),
        verification_id=verification.id,
        step_number=1,
        step_type=VerificationStepType.TOOL_CALL,
        tool_name="log_search",
        input_data={"query": "test"},
        status="COMPLETED"
    )
    db_session.add(step)
    await db_session.flush()

    # 4. Test Evidence and HypothesisEvidence with origins
    evidence = Evidence(
        id=str(uuid.uuid4()),
        investigation_run_id=run.id,
        source_type=EvidenceSourceType.LOG,
        content="log result",
        source_name="syslog"
    )
    db_session.add(evidence)
    await db_session.flush()

    mapping_initial = HypothesisEvidence(
        hypothesis_id=hypothesis.id,
        evidence_id=evidence.id,
        relationship=EvidenceRelationshipType.SUPPORTS,
        strength=EvidenceStrength.HIGH,
        origin="INITIAL"
    )
    db_session.add(mapping_initial)
    
    mapping_verification = HypothesisEvidence(
        hypothesis_id=hypothesis.id,
        evidence_id=evidence.id,
        relationship=EvidenceRelationshipType.CONTRADICTS,
        strength=EvidenceStrength.LOW,
        origin="VERIFICATION",
        verification_id=verification.id
    )
    db_session.add(mapping_verification)
    await db_session.flush()

    # 5. Commit and verify Cascade behavior
    await db_session.commit()

    # Check persistence
    v = await db_session.get(HypothesisVerification, verification.id)
    assert v is not None
    assert v.status == "RUNNING"
    assert v.hypothesis_id == hypothesis.id

    # Cascade test
    await db_session.delete(hypothesis)
    await db_session.commit()

    # If cascading works, verification should be gone
    v_deleted = await db_session.get(HypothesisVerification, verification.id)
    assert v_deleted is None

    # Step should be gone
    step_deleted = await db_session.get(VerificationStep, step.id)
    assert step_deleted is None

    # Mappings should be gone
    result = await db_session.execute(select(HypothesisEvidence).where(HypothesisEvidence.hypothesis_id == hypothesis.id))
    mappings = result.scalars().all()
    assert len(mappings) == 0

    print("Postgres Integration tests passed: Tables, ENUMs, Mappings, and Cascades verified.")
