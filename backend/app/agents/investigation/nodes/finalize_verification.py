import json
from typing import Dict, Any
from app.agents.investigation.state import InvestigationState
from app.models.hypothesis import EvidenceRelationshipType, HypothesisStatus
from langchain_core.messages import SystemMessage

def get_strength_value(strength: str) -> float:
    values = {"LOW": 1.0, "MEDIUM": 2.0, "HIGH": 3.0}
    return values.get(strength, 0.0)

def finalize_verification(state: InvestigationState) -> Dict[str, Any]:
    verification = state.get("verification", {})
    if not verification:
        return {"current_step": "select_hypothesis_for_verification"}
        
    hypothesis_id = verification.get("hypothesis_id")
    if not hypothesis_id:
        return {"current_step": "select_hypothesis_for_verification"}
        
    supporting_ids = verification.get("supporting_evidence_ids", [])
    contradicting_ids = verification.get("contradicting_evidence_ids", [])
    
    # We will map these to state["hypothesis_evidence_mappings"]
    existing_mappings = state.get("hypothesis_evidence_mappings", [])
    evidence_list = state.get("evidence", [])
    
    # Create lookup for fast validation and extraction
    evidence_lookup = {ev["id"]: ev for ev in evidence_list if "id" in ev}
    
    new_mappings = list(existing_mappings)
    
    support_delta = 0.0
    contradiction_penalty = 0.0
    
    # Process supporting
    for eid in supporting_ids:
        # Avoid double counting if already mapped for this hypothesis
        # But wait, existing mappings use hypothesis_temp_id or hypothesis_id?
        # In phase 6 they used temp_id. But later they might have actual IDs.
        # Let's check both.
        is_duplicate = False
        for m in new_mappings:
            if m.get("evidence_id") == eid and (m.get("hypothesis_temp_id") == hypothesis_id or m.get("hypothesis_id") == hypothesis_id):
                is_duplicate = True
                break
        
        if is_duplicate:
            continue
            
        if eid in evidence_lookup:
            ev = evidence_lookup[eid]
            eval_data = ev.get("verification_eval", {})
            strength = eval_data.get("strength", "LOW")
            reason = eval_data.get("reasoning", "Verification support")
            
            new_mappings.append({
                "hypothesis_temp_id": hypothesis_id,
                "hypothesis_id": hypothesis_id, # Can set both just in case
                "evidence_id": eid,
                "relationship": EvidenceRelationshipType.SUPPORTS.value,
                "strength": strength,
                "reason": reason,
                "origin": "VERIFICATION"
            })
            support_delta += get_strength_value(strength)
            
    # Process contradicting
    for eid in contradicting_ids:
        is_duplicate = False
        for m in new_mappings:
            if m.get("evidence_id") == eid and (m.get("hypothesis_temp_id") == hypothesis_id or m.get("hypothesis_id") == hypothesis_id):
                is_duplicate = True
                break
                
        if is_duplicate:
            continue
            
        if eid in evidence_lookup:
            ev = evidence_lookup[eid]
            eval_data = ev.get("verification_eval", {})
            strength = eval_data.get("strength", "LOW")
            reason = eval_data.get("reasoning", "Verification contradiction")
            
            new_mappings.append({
                "hypothesis_temp_id": hypothesis_id,
                "hypothesis_id": hypothesis_id,
                "evidence_id": eid,
                "relationship": EvidenceRelationshipType.CONTRADICTS.value,
                "strength": strength,
                "reason": reason,
                "origin": "VERIFICATION"
            })
            contradiction_penalty += get_strength_value(strength)
            
    # Calculate outcome
    net_delta = support_delta - contradiction_penalty
    
    if net_delta >= 3.0 and contradiction_penalty <= 2.0:
        outcome = HypothesisStatus.SUPPORTED.value
    elif net_delta <= -3.0 or contradiction_penalty >= 4.0:
        outcome = HypothesisStatus.WEAKENED.value
    else:
        outcome = HypothesisStatus.INCONCLUSIVE.value
        
    # Update hypothesis status in state
    hypotheses = list(state.get("hypotheses", []))
    for h in hypotheses:
        if h.get("temp_id") == hypothesis_id or h.get("id") == hypothesis_id:
            h["status"] = outcome
            # We don't update score here, rank_hypotheses will do it based on mappings
            break
            
    # Update verification summary
    summary = f"Verification completed. Found {len(supporting_ids)} supporting and {len(contradicting_ids)} contradicting signals. Net delta: {net_delta}. Outcome: {outcome}."
    
    # Clean up verification state
    new_verification = verification.copy()
    new_verification["status"] = "COMPLETED"
    new_verification["support_delta"] = support_delta
    new_verification["contradiction_delta"] = contradiction_penalty
    new_verification["summary"] = summary
    
    completed_verifications = state.get("completed_verifications", [])
    
    return {
        "current_step": "rank_hypotheses",
        "hypotheses": hypotheses,
        "hypothesis_evidence_mappings": new_mappings,
        "verification": new_verification,
        "completed_verifications": completed_verifications + [hypothesis_id],
        "messages": [SystemMessage(content=summary)]
    }
