import pytest
from app.tools.incident_context import IncidentContextAnalyzer

@pytest.mark.asyncio
async def test_incident_context_analyzer_schema():
    tool = IncidentContextAnalyzer()
    assert tool.name == "incident_context_analyzer"
    assert "incident_id" in tool.input_schema["properties"]
