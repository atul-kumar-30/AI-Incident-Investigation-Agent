import pytest
import pytest_asyncio
import os
from httpx import AsyncClient
from app.models.incident import Incident

# Skip if LLM_API_KEY is not set to a real key
pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.integration,
    pytest.mark.skipif(
        os.environ.get("LLM_API_KEY", "MOCK_KEY") in ("MOCK_KEY", "your_gemini_api_key", ""),
        reason="Real LLM_API_KEY required for integration tests"
    )
]

@pytest_asyncio.fixture
async def test_incident(db_session):
    incident = Incident(
        title="Database Timeout on Login",
        description="Users are reporting timeout errors when trying to log in. The auth service seems to be timing out when connecting to the database pool.",
        severity="HIGH",
        source="MANUAL"
    )
    db_session.add(incident)
    await db_session.commit()
    await db_session.refresh(incident)
    yield incident

async def test_real_llm_investigation(client: AsyncClient, test_incident):
    """
    Integration test to verify that the REAL Gemini planner can successfully route
    and use the tools we've provided in Phase 3.
    """
    # 1. Start investigation
    response = await client.post(f"/api/v1/incidents/{test_incident.id}/investigations")
    assert response.status_code == 201
    run_id = response.json()["id"]
    
    # 2. Wait for it to complete
    import asyncio
    for _ in range(45): # Real LLM might take longer
        res = await client.get(f"/api/v1/investigations/{run_id}")
        if res.json()["status"] in ["COMPLETED", "FAILED"]:
            break
        await asyncio.sleep(2)
        
    final_res = await client.get(f"/api/v1/investigations/{run_id}")
    data = final_res.json()
    
    # Assert it finished successfully
    assert data["status"] == "COMPLETED"
    
    # Verify it pulled some evidence (from context or logs)
    ev_res = await client.get(f"/api/v1/investigations/{run_id}/evidence")
    evidence = ev_res.json()
    assert len(evidence) > 0
