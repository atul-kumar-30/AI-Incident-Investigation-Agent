import pytest
from app.agents.investigation.state import InvestigationState
from app.agents.investigation.nodes.evaluate_verification_evidence import evaluate_verification_evidence
from app.agents.investigation.nodes.finalize_verification import finalize_verification
from app.agents.investigation.nodes.verification_planner import verification_planner
from app.agents.investigation.nodes.select_hypothesis_for_verification import select_hypothesis_for_verification
from app.agents.investigation.nodes.rank_hypotheses import rank_hypotheses
from app.models.hypothesis import EvidenceRelationshipType, HypothesisStatus
from app.agents.investigation.llm import FakeStructuredLLM

@pytest.mark.asyncio
async def test_evaluate_verification_evidence_supports():
    # Force the mock to return SUPPORTS
    FakeStructuredLLM.call_count = 0
    state = InvestigationState(
        current_step="evaluate_verification_evidence",
        verification={"status": "RUNNING", "hypothesis_title": "Test", "hypothesis_description": "Test", "new_evidence_ids": ["ev_1"], "tool_history": [{"objective": "test", "expected_signal": "test", "contradicting_signal": "test"}]},
        evidence=[{"id": "ev_1", "content": "test log"}]
    )
    
    result = await evaluate_verification_evidence(state)
    assert result["current_step"] == "verification_planner"
    assert "ev_1" in result["verification"]["supporting_evidence_ids"]
    assert "ev_1" not in result["verification"]["contradicting_evidence_ids"]
    assert len(result["verification"]["new_evidence_ids"]) == 0

def test_finalize_verification_supported_outcome():
    state = InvestigationState(
        current_step="finalize_verification",
        verification={
            "status": "RUNNING",
            "hypothesis_id": "h_1",
            "supporting_evidence_ids": ["ev_1"],
            "contradicting_evidence_ids": []
        },
        evidence=[{"id": "ev_1", "verification_eval": {"strength": "HIGH", "relationship": "SUPPORTS"}}],
        hypotheses=[{"temp_id": "h_1", "status": "PROPOSED"}],
        hypothesis_evidence_mappings=[]
    )
    result = finalize_verification(state)
    
    assert result["current_step"] == "rank_hypotheses"
    assert result["verification"]["status"] == "COMPLETED"
    assert result["verification"]["support_delta"] == 3.0
    assert result["verification"]["contradiction_delta"] == 0.0
    
    # Net delta = 3.0, outcome = SUPPORTED
    h = next(h for h in result["hypotheses"] if h["temp_id"] == "h_1")
    assert h["status"] == HypothesisStatus.SUPPORTED.value
    
    # Check mapping
    assert len(result["hypothesis_evidence_mappings"]) == 1
    m = result["hypothesis_evidence_mappings"][0]
    assert m["evidence_id"] == "ev_1"
    assert m["origin"] == "VERIFICATION"

def test_finalize_verification_weakened_outcome():
    state = InvestigationState(
        current_step="finalize_verification",
        verification={
            "status": "RUNNING",
            "hypothesis_id": "h_1",
            "supporting_evidence_ids": [],
            "contradicting_evidence_ids": ["ev_2", "ev_3"]
        },
        evidence=[
            {"id": "ev_2", "verification_eval": {"strength": "HIGH", "relationship": "CONTRADICTS"}},
            {"id": "ev_3", "verification_eval": {"strength": "LOW", "relationship": "CONTRADICTS"}}
        ],
        hypotheses=[{"temp_id": "h_1", "status": "PROPOSED"}],
        hypothesis_evidence_mappings=[]
    )
    result = finalize_verification(state)
    
    assert result["verification"]["support_delta"] == 0.0
    assert result["verification"]["contradiction_delta"] == 4.0  # 3.0 + 1.0
    
    h = next(h for h in result["hypotheses"] if h["temp_id"] == "h_1")
    assert h["status"] == HypothesisStatus.WEAKENED.value

def test_finalize_verification_inconclusive_outcome():
    state = InvestigationState(
        current_step="finalize_verification",
        verification={
            "status": "RUNNING",
            "hypothesis_id": "h_1",
            "supporting_evidence_ids": ["ev_1"],
            "contradicting_evidence_ids": ["ev_2"]
        },
        evidence=[
            {"id": "ev_1", "verification_eval": {"strength": "HIGH", "relationship": "SUPPORTS"}},
            {"id": "ev_2", "verification_eval": {"strength": "HIGH", "relationship": "CONTRADICTS"}}
        ],
        hypotheses=[{"temp_id": "h_1", "status": "PROPOSED"}],
        hypothesis_evidence_mappings=[]
    )
    result = finalize_verification(state)
    
    # Net delta = 0
    h = next(h for h in result["hypotheses"] if h["temp_id"] == "h_1")
    assert h["status"] == HypothesisStatus.INCONCLUSIVE.value

def test_duplicate_evidence_prevention():
    state = InvestigationState(
        current_step="finalize_verification",
        verification={
            "status": "RUNNING",
            "hypothesis_id": "h_1",
            "supporting_evidence_ids": ["ev_1"]
        },
        evidence=[{"id": "ev_1", "verification_eval": {"strength": "HIGH", "relationship": "SUPPORTS"}}],
        hypotheses=[{"temp_id": "h_1", "status": "PROPOSED"}],
        hypothesis_evidence_mappings=[{
            "hypothesis_temp_id": "h_1",
            "evidence_id": "ev_1",
            "relationship": "SUPPORTS",
            "origin": "INITIAL"
        }]
    )
    result = finalize_verification(state)
    
    assert len(result["hypothesis_evidence_mappings"]) == 1
    assert result["verification"]["support_delta"] == 0.0

def test_verification_planner_iteration_limit():
    state = InvestigationState(
        current_step="verification_planner",
        verification={
            "status": "RUNNING",
            "iteration_count": 4,
            "max_iterations": 4
        }
    )
    result = verification_planner(state)
    assert result["current_step"] == "finalize_verification"

def test_verification_planner_budget_enforcement():
    state = InvestigationState(
        current_step="verification_planner",
        verification={
            "status": "RUNNING",
            "iteration_count": 0,
            "max_iterations": 4,
            "tool_budgets": {"log_search": 0}
        }
    )
    FakeStructuredLLM.call_count = 0  # mock returns log_search
    result = verification_planner(state)
    assert result["current_step"] == "finalize_verification"
    assert result["messages"][0].content.find("decided to finish") != -1

def test_verification_planner_duplicate_query_prevention():
    state = InvestigationState(
        current_step="verification_planner",
        verification={
            "status": "RUNNING",
            "iteration_count": 0,
            "max_iterations": 4,
            "tool_budgets": {"log_search": 5},
            "tool_history": [
                {
                    "tool_name": "log_search",
                    "input_data": {"incident_id": "auto", "query": "verification search", "limit": 10}
                }
            ]
        }
    )
    FakeStructuredLLM.call_count = 0  # mock returns log_search with same input
    result = verification_planner(state)
    assert result["current_step"] == "finalize_verification"
    assert result["messages"][0].content.find("Duplicate") != -1

def test_reranking_after_verification():
    state = InvestigationState(
        current_step="rank_hypotheses",
        hypotheses=[
            {"temp_id": "h_1", "status": "SUPPORTED", "title": "H1", "score": 10},
            {"temp_id": "h_2", "status": "PROPOSED", "title": "H2", "score": 10}
        ],
        evidence=[{"id": "ev_1"}],
        hypothesis_evidence_mappings=[
            {"hypothesis_temp_id": "h_1", "evidence_id": "ev_1", "relationship": "SUPPORTS", "strength": "HIGH", "origin": "VERIFICATION"}
        ]
    )
    result = rank_hypotheses(state)
    # H1 should get a verification score bump over H2
    h1 = next(h for h in result["hypotheses"] if h["temp_id"] == "h_1")
    h2 = next(h for h in result["hypotheses"] if h["temp_id"] == "h_2")
    assert h1["preliminary_score"] > h2["preliminary_score"]
    assert h1["rank"] == 1

def test_duplicate_verification_prevention():
    state = InvestigationState(
        current_step="select_hypothesis_for_verification",
        hypotheses=[
            {"temp_id": "h_1", "status": "SUPPORTED", "rank": 1},
            {"temp_id": "h_2", "status": "PROPOSED", "rank": 2}
        ],
        completed_verifications=["h_1"]
    )
    result = select_hypothesis_for_verification(state)
    assert result["verification"]["hypothesis_id"] == "h_2"

def test_verification_state_reset():
    state = InvestigationState(
        current_step="select_hypothesis_for_verification",
        hypotheses=[{"temp_id": "h_1", "status": "PROPOSED", "rank": 1}],
        completed_verifications=[],
        verification={"status": "COMPLETED", "hypothesis_id": "old"}
    )
    result = select_hypothesis_for_verification(state)
    assert result["verification"]["hypothesis_id"] == "h_1"
    assert result["verification"]["iteration_count"] == 0
    assert result["verification"]["tool_history"] == []
    assert result["verification"]["supporting_evidence_ids"] == []

