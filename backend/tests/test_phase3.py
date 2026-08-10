import pytest
import pytest_asyncio
from httpx import AsyncClient
from app.models.incident import Incident

pytestmark = pytest.mark.asyncio

@pytest_asyncio.fixture
async def test_incident(db_session):
    incident = Incident(title="Phase3 Test", description="Test", severity="HIGH", source="MANUAL")
    db_session.add(incident)
    await db_session.commit()
    await db_session.refresh(incident)
    yield incident

async def test_log_ingestion_and_search_tool(client: AsyncClient, test_incident):
    # Ingest Logs
    payload = {
        "logs": [
            {
                "timestamp": "2026-08-09T10:00:00Z",
                "level": "ERROR",
                "service": "auth-service",
                "message": "Timeout to database",
                "endpoint": "/login",
                "http_status": 500
            },
            {
                "timestamp": "2026-08-09T10:00:01Z",
                "level": "INFO",
                "service": "auth-service",
                "message": "User logged in",
                "endpoint": "/login",
                "http_status": 200
            }
        ]
    }
    
    response = await client.post(f"/api/v1/incidents/{test_incident.id}/logs", json=payload)
    assert response.status_code == 201
    
    # Test Search API
    response = await client.get(f"/api/v1/incidents/{test_incident.id}/logs?query=timeout")
    assert response.status_code == 200
    logs = response.json()
    assert len(logs) == 1
    assert logs[0]["message"] == "Timeout to database"

async def test_investigation_loop(client: AsyncClient, test_incident):
    # 1. Start investigation
    response = await client.post(f"/api/v1/incidents/{test_incident.id}/investigations")
    if response.status_code != 201:
        print(response.json())
    assert response.status_code == 201
    run_id = response.json()["id"]
    
    # 2. Wait for it to complete
    import asyncio
    for _ in range(15):
        res = await client.get(f"/api/v1/investigations/{run_id}")
        if res.json()["status"] in ["COMPLETED", "FAILED"]:
            break
        await asyncio.sleep(1)
        
    final_res = await client.get(f"/api/v1/investigations/{run_id}")
    data = final_res.json()
    
    if data["status"] != "COMPLETED":
        steps_res = await client.get(f"/api/v1/investigations/{run_id}/steps")
        print("Steps:", steps_res.json())
        print("Data:", data)
        
    assert data["status"] == "COMPLETED"
    
    # 3. Verify iteration loop and LOG evidence
    steps_res = await client.get(f"/api/v1/investigations/{run_id}/steps")
    steps = steps_res.json()
    assert len(steps) > 3
    
    ev_res = await client.get(f"/api/v1/investigations/{run_id}/evidence")
    evidence = ev_res.json()
    assert len(evidence) > 0
    
    log_evidence = [e for e in evidence if e["source_type"] == "LOG"]
    if log_evidence:
        assert log_evidence[0]["source_name"] == "log_search"
