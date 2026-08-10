from typing import Dict, Any
from app.agents.investigation.state import InvestigationState
from app.models.hypothesis import EvidenceRelationshipType
from langchain_core.messages import HumanMessage

def calculate_source_diversity_bonus(hypothesis_temp_id: str, mappings: list, evidence_lookup: dict) -> float:
    """Calculates a bounded source diversity bonus"""
    supporting_sources = set()
    for m in mappings:
        if m["hypothesis_temp_id"] == hypothesis_temp_id and m["relationship"] == EvidenceRelationshipType.SUPPORTS.value:
            eid = m["evidence_id"]
            if eid in evidence_lookup:
                supporting_sources.add(evidence_lookup[eid].get("source_type"))
    
    # 0.5 bonus for each independent source beyond the first, max +1.5 (e.g. 4 sources)
    if not supporting_sources:
        return 0.0
    return min((len(supporting_sources) - 1) * 0.5, 1.5)

def get_strength_value(strength: str) -> float:
    values = {"LOW": 1.0, "MEDIUM": 2.0, "HIGH": 3.0}
    return values.get(strength, 0.0)

def rank_hypotheses(state: InvestigationState) -> Dict[str, Any]:
    """
    Deterministically scores and ranks hypotheses based on evidence mappings.
    """
    hypotheses = state.get("hypotheses", [])
    mappings = state.get("hypothesis_evidence_mappings", [])
    evidence_list = state.get("evidence", [])
    
    evidence_lookup = {ev["id"]: ev for ev in evidence_list if "id" in ev}
    
    # Score hypotheses
    for h in hypotheses:
        temp_id = h.get("temp_id")
        
        support_score = 0.0
        contradiction_score = 0.0
        
        for m in mappings:
            if m["hypothesis_temp_id"] == temp_id:
                val = get_strength_value(m["strength"])
                if m["relationship"] == EvidenceRelationshipType.SUPPORTS.value:
                    support_score += val
                elif m["relationship"] == EvidenceRelationshipType.CONTRADICTS.value:
                    contradiction_score -= val
                    
        diversity_bonus = calculate_source_diversity_bonus(temp_id, mappings, evidence_lookup)
        
        # Raw score
        h["support_score"] = support_score
        h["contradiction_score"] = contradiction_score
        h["source_diversity_bonus"] = diversity_bonus
        
        h["raw_score"] = support_score + contradiction_score + diversity_bonus
    
    # Sort descending by raw_score
    # In case of tie, sort by number of supporting evidence
    def sort_key(h):
        support_count = sum(1 for m in mappings if m["hypothesis_temp_id"] == h["temp_id"] and m["relationship"] == EvidenceRelationshipType.SUPPORTS.value)
        return (h["raw_score"], support_count)
        
    ranked_hypotheses = sorted(hypotheses, key=sort_key, reverse=True)
    
    # Assign ranks and normalized scores
    # Normalization (0-100) is simple mapping: we assume a decent score is around 10, let's map it reasonably or just cap at 100.
    # A simple approach: score / max_score * 100, but max_score depends on evidence count.
    # Let's just use a sigmoid-like or bounded mapping, or simply raw_score * 10 (capped at 100).
    for i, h in enumerate(ranked_hypotheses):
        h["rank"] = i + 1
        # Simple normalization for preliminary score
        norm_score = max(0, min(int(h["raw_score"] * 10), 100))
        h["preliminary_score"] = norm_score
    
    # We will pass them back to state so `investigation_service.py` can persist them.
    # Note: `temp_id` will be used to link them up when persisting.
    
    # Build a summary of the ranking to put in messages
    summary_parts = [f"Ranked {len(ranked_hypotheses)} hypotheses."]
    if ranked_hypotheses:
        summary_parts.append(f"Leading candidate: {ranked_hypotheses[0]['title']} (Score: {ranked_hypotheses[0]['preliminary_score']})")
        
    return {
        "hypotheses": ranked_hypotheses,
        "current_step": "rank_hypotheses",
        "messages": [HumanMessage(content="\n".join(summary_parts))]
    }
