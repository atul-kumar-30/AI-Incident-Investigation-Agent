from typing import Dict, Any, List
from app.agents.investigation.state import InvestigationState
from app.models.hypothesis import EvidenceRelationshipType, EvidenceStrength
from langchain_core.messages import HumanMessage

def classify_evidence_strength(source_type: str, relationship: str) -> EvidenceStrength:
    """
    Deterministic rule to assign strength based on source type and relationship.
    This is a simple baseline.
    """
    if relationship == EvidenceRelationshipType.SUPPORTS.value:
        if source_type in ("LOG", "METRIC", "GIT_CHANGE"):
            return EvidenceStrength.HIGH
        elif source_type == "CODE":
            return EvidenceStrength.MEDIUM
        return EvidenceStrength.LOW
    elif relationship == EvidenceRelationshipType.CONTRADICTS.value:
        if source_type in ("LOG", "METRIC"):
            return EvidenceStrength.HIGH
        return EvidenceStrength.MEDIUM
    return EvidenceStrength.LOW

def map_evidence(state: InvestigationState) -> Dict[str, Any]:
    """
    Validates IDs, classifies relationships, assigns strength, and prepares mappings for ranking.
    """
    hypotheses = state.get("hypotheses", [])
    evidence_list = state.get("evidence", [])
    
    # Create lookup for fast validation and source type extraction
    evidence_lookup = {ev["id"]: ev for ev in evidence_list if "id" in ev}
    
    mappings = []
    messages = []
    
    for h_idx, h in enumerate(hypotheses):
        # We need a temporary ID to link mappings before DB persistence
        h["temp_id"] = f"temp_h_{h_idx}"
        
        # Support
        for eid in h.get("supporting_evidence_ids", []):
            if eid in evidence_lookup:
                source_type = evidence_lookup[eid].get("source_type")
                mappings.append({
                    "hypothesis_temp_id": h["temp_id"],
                    "evidence_id": eid,
                    "relationship": EvidenceRelationshipType.SUPPORTS.value,
                    "strength": classify_evidence_strength(source_type, EvidenceRelationshipType.SUPPORTS.value).value,
                    "reason": f"Identified as supporting evidence from {source_type}"
                })
        
        # Contradicts
        for eid in h.get("contradicting_evidence_ids", []):
            # Ensure not mapping same evidence as both
            if any(m["evidence_id"] == eid and m["hypothesis_temp_id"] == h["temp_id"] for m in mappings):
                continue
                
            if eid in evidence_lookup:
                source_type = evidence_lookup[eid].get("source_type")
                mappings.append({
                    "hypothesis_temp_id": h["temp_id"],
                    "evidence_id": eid,
                    "relationship": EvidenceRelationshipType.CONTRADICTS.value,
                    "strength": classify_evidence_strength(source_type, EvidenceRelationshipType.CONTRADICTS.value).value,
                    "reason": f"Identified as contradicting evidence from {source_type}"
                })

    messages.append(HumanMessage(content=f"Mapped {len(mappings)} evidence relationships."))

    return {
        "hypothesis_evidence_mappings": mappings,
        "hypotheses": hypotheses, # Updated with temp_ids
        "current_step": "map_evidence",
        "messages": messages
    }
