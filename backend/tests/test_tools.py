import pytest
from app.tools.incident_context import IncidentContextAnalyzer

@pytest.mark.asyncio
async def test_incident_context_analyzer_schema():
    tool = IncidentContextAnalyzer()
    assert tool.name == "incident_context_analyzer"
    assert "incident_id" in tool.input_schema["properties"]

def test_registry_contains_all_tools():
    from app.tools.registry import registry
    tools = registry.get_all_tools()
    assert "incident_context_analyzer" in tools
    assert "log_search" in tools
    assert "code_search" in tools
    assert "recent_changes" in tools
    assert "docs_search" in tools
