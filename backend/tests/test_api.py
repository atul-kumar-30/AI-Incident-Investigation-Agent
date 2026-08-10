import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_health_check(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

async def test_create_incident(client: AsyncClient):
    data = {
        "title": "Test Incident",
        "description": "Test Description",
        "severity": "HIGH"
    }
    response = await client.post("/api/v1/incidents", json=data)
    assert response.status_code == 201
    result = response.json()
    assert result["title"] == "Test Incident"
    assert result["status"] == "OPEN"
    assert result["severity"] == "HIGH"
    assert result["source"] == "API"
    assert "id" in result

async def test_get_incidents(client: AsyncClient):
    response = await client.get("/api/v1/incidents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

async def test_get_incident(client: AsyncClient):
    data = {"title": "Test Get", "description": "Desc"}
    create_resp = await client.post("/api/v1/incidents", json=data)
    incident_id = create_resp.json()["id"]

    get_resp = await client.get(f"/api/v1/incidents/{incident_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == incident_id

async def test_update_incident(client: AsyncClient):
    data = {"title": "Test Update", "description": "Desc"}
    create_resp = await client.post("/api/v1/incidents", json=data)
    incident_id = create_resp.json()["id"]

    update_data = {"status": "INVESTIGATING", "severity": "CRITICAL"}
    update_resp = await client.patch(f"/api/v1/incidents/{incident_id}", json=update_data)
    assert update_resp.status_code == 200
    result = update_resp.json()
    assert result["status"] == "INVESTIGATING"
    assert result["severity"] == "CRITICAL"

async def test_delete_incident(client: AsyncClient):
    data = {"title": "Test Delete", "description": "Desc"}
    create_resp = await client.post("/api/v1/incidents", json=data)
    incident_id = create_resp.json()["id"]

    delete_resp = await client.delete(f"/api/v1/incidents/{incident_id}")
    assert delete_resp.status_code == 204

    get_resp = await client.get(f"/api/v1/incidents/{incident_id}")
    assert get_resp.status_code == 404

async def test_invalid_incident_data(client: AsyncClient):
    data = {"title": "Test Invalid"}  # Missing description
    response = await client.post("/api/v1/incidents", json=data)
    assert response.status_code == 422
