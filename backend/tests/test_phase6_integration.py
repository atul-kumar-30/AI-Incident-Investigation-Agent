import pytest
import asyncio
from app.agents.investigation.graph import investigation_graph
from app.agents.investigation.state import InvestigationState
from app.models.incident import IncidentSeverity, IncidentSource

@pytest.mark.asyncio
async def test_canonical_e2e_phase6():
    from app.agents.investigation.llm import FakeStructuredLLM
    FakeStructuredLLM.call_count = 0
    
    state = InvestigationState(
        incident_id="test-incident",
        incident_title="High Error Rate on Login API",
        incident_description="Users are reporting 500 errors when attempting to log in. Alerts show a spike in failed requests to /api/v1/auth/login.",
        incident_severity=IncidentSeverity.CRITICAL.value,
        incident_source=IncidentSource.MANUAL.value,
        evidence=[],
        hypotheses=[],
        hypothesis_evidence_mappings=[],
        tool_requests=[],
        current_step="initialize",
        iteration_count=0,
        max_iterations=5,
        tool_budget={"search_logs": 3, "search_code": 3, "get_recent_commits": 2, "search_documents": 2}
    )
    
    # Run the graph
    result = await investigation_graph.ainvoke(state)
    
    # Output verification
    assert "hypotheses" in result
    assert len(result["hypotheses"]) > 0
    assert "rank" in result["hypotheses"][0]
    
    # Just print the leading hypothesis
    leading = result["hypotheses"][0]
    print(f"\nLeading Hypothesis: {leading['title']} (Score: {leading['preliminary_score']})")
    print(f"Reasoning: {leading['reasoning_summary']}")
