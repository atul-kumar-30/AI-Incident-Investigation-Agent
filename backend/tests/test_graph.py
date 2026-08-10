import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.agents.investigation.graph import investigation_graph

@pytest.mark.asyncio
async def test_graph_deterministic_flow():
    # We will just verify the graph structure compiles and has correct nodes
    assert "planner" in investigation_graph.nodes
    assert "execute_tool" in investigation_graph.nodes
    assert "record_evidence" in investigation_graph.nodes
    assert "finalize" in investigation_graph.nodes
    assert "initialize" in investigation_graph.nodes
