import uuid
from typing import Dict, Any
from app.agents.investigation.state import InvestigationState, VerificationState
from app.models.hypothesis import HypothesisStatus
from langchain_core.messages import SystemMessage

MAX_HYPOTHESES_TO_VERIFY = 3

def select_hypothesis_for_verification(state: InvestigationState) -> Dict[str, Any]:
    """
    Selects the next hypothesis to verify.
    Resets the verification state cleanly.
    """
    hypotheses = state.get("hypotheses", [])
    completed = state.get("completed_verifications", [])
    target_id = state.get("target_hypothesis_id")
    
    # Sort hypotheses by rank ascending
    sorted_hypotheses = sorted(
        [h for h in hypotheses if h.get("rank") is not None],
        key=lambda h: h["rank"]
    )
    
    selected_h = None
    
    if target_id:
        # Manual verification mode
        if target_id in completed:
            selected_h = None # Already verified this run
        else:
            for h in sorted_hypotheses:
                if h.get("temp_id") == target_id or h.get("id") == target_id:
                    selected_h = h
                    break
    else:
        # Automatic top-3 mode
        if len(completed) >= MAX_HYPOTHESES_TO_VERIFY:
            selected_h = None
        else:
            for h in sorted_hypotheses:
                hid = h.get("temp_id") or h.get("id")
                status = h.get("status", HypothesisStatus.PROPOSED.value)
                if hid not in completed and status == HypothesisStatus.PROPOSED.value:
                    selected_h = h
                    break
                    
    if not selected_h:
        # No more hypotheses to verify
        return {
            "current_step": "finalize",
            "messages": [SystemMessage(content="Verification phase complete.")]
        }
        
    hid = selected_h.get("temp_id") or selected_h.get("id")
    
    # Initialize a clean verification state
    verification_state: VerificationState = {
        "verification_id": str(uuid.uuid4()),
        "hypothesis_id": hid,
        "hypothesis_title": selected_h.get("title", ""),
        "hypothesis_description": selected_h.get("description", ""),
        "hypothesis_category": selected_h.get("category", ""),
        "current_score": selected_h.get("preliminary_score", 0.0),
        "verification_requirements": selected_h.get("verification_requirements", []),
        "missing_evidence": selected_h.get("missing_evidence", []),
        "selected_requirement": "",
        "tool_history": [],
        "new_evidence_ids": [],
        "supporting_evidence_ids": [],
        "contradicting_evidence_ids": [],
        "iteration_count": 0,
        "max_iterations": 4,
        "tool_budgets": {
            "search_logs": 2,
            "search_code": 2,
            "get_recent_commits": 1,
            "search_documents": 1
        },
        "status": "RUNNING",
        "errors": []
    }
    
    return {
        "current_step": "verification_planner",
        "verification": verification_state,
        "messages": [SystemMessage(content=f"Starting verification for hypothesis: {verification_state['hypothesis_title']}")]
    }
