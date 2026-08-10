import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_start_investigation_nonexistent(client: AsyncClient):
    response = await client.post("/api/v1/incidents/nonexistent_id/investigations")
    assert response.status_code == 404
