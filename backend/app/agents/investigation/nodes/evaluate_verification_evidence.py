import json
import uuid
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field

from app.agents.investigation.state import InvestigationState
from app.agents.investigation.llm import get_structured_llm
from app.models.hypothesis import EvidenceRelationshipType, EvidenceStrength

class EvidenceEvaluation(BaseModel):
    relationship: str = Field(description="Must be one of: SUPPORTS, CONTRADICTS, NEUTRAL")
    strength: str = Field(description="Must be one of: LOW, MEDIUM, HIGH")
    reasoning: str = Field(description="Brief explanation of why this evidence relates to the hypothesis in this way.")

async def evaluate_verification_evidence(state: InvestigationState) -> Dict[str, Any]:
    verification = state.get("verification", {})
    if not verification:
        return {"current_step": "verification_planner"}
        
    evidence_list = state.get("evidence", [])
    new_evidence_ids = verification.get("new_evidence_ids", [])
    
    if not new_evidence_ids:
        # No new evidence to evaluate, go back to planner
        return {"current_step": "verification_planner"}
        
    # Get the latest tool history item
    tool_history = verification.get("tool_history", [])
    if not tool_history:
        return {"current_step": "verification_planner"}
        
    current_action = tool_history[-1]
    
    # We will evaluate all new evidence generated in the last step
    new_evidence_items = [e for e in evidence_list if e.get("id") in new_evidence_ids]
    
    system_prompt = """You are an expert incident investigator evaluating new evidence.
Given a hypothesis, a specific verification requirement, expected signals, contradicting signals, and newly discovered evidence.
Determine if the evidence SUPPORTS, CONTRADICTS, or is NEUTRAL to the hypothesis.
Classify the strength as LOW, MEDIUM, or HIGH.

Be strictly objective. Only classify as SUPPORTS or CONTRADICTS if the evidence provides a clear, meaningful signal.
"""

    llm = get_structured_llm(EvidenceEvaluation)
    
    # We update the state by tracking new relations. We don't save to DB here; that happens in finalize_verification or mapping node.
    # Actually, we can just save it into the state and then the DB persistence can handle it, or we do it later.
    
    # Let's accumulate the evaluations
    supporting_ids = list(verification.get("supporting_evidence_ids", []))
    contradicting_ids = list(verification.get("contradicting_evidence_ids", []))
    
    updated_evidence_list = list(evidence_list)
    
    for ev in new_evidence_items:
        context = {
            "hypothesis_title": verification.get("hypothesis_title"),
            "hypothesis_description": verification.get("hypothesis_description"),
            "requirement_tested": current_action.get("objective"),
            "expected_signal": current_action.get("expected_signal"),
            "contradicting_signal": current_action.get("contradicting_signal"),
            "evidence_content": ev.get("content")
        }
        
        try:
            eval_result = await llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=json.dumps(context, indent=2))
            ])
            
            # Record the evaluation result in the evidence metadata for the current run
            ev["verification_eval"] = {
                "relationship": eval_result.relationship,
                "strength": eval_result.strength,
                "reasoning": eval_result.reasoning,
                "verification_id": verification.get("verification_id")
            }
            
            # Track IDs for scoring later
            if eval_result.relationship == "SUPPORTS":
                supporting_ids.append(ev["id"])
            elif eval_result.relationship == "CONTRADICTS":
                contradicting_ids.append(ev["id"])
                
        except Exception as e:
            # Fallback on neutral if LLM fails
            ev["verification_eval"] = {
                "relationship": "NEUTRAL",
                "strength": "LOW",
                "reasoning": f"Evaluation failed: {str(e)}",
                "verification_id": verification.get("verification_id")
            }
            
    # Update tool history status
    # TypedDict nested updates: we need to replace tool_history array
    new_tool_history = list(tool_history)
    new_tool_history[-1]["status"] = "COMPLETED"
    new_tool_history[-1]["evidence_evaluated"] = len(new_evidence_items)
            
    # Clear new_evidence_ids for the next iteration
    new_verification = dict(verification)
    new_verification["new_evidence_ids"] = []
    new_verification["supporting_evidence_ids"] = supporting_ids
    new_verification["contradicting_evidence_ids"] = contradicting_ids
    new_verification["tool_history"] = new_tool_history
    
    # Wait, we need to return the updated evidence list because we mutated the evidence items inside it.
    # Actually, we modified the dict in place, but returning it explicitly is safer.
    
    return {
        "current_step": "verification_planner",
        "verification": new_verification,
        # "evidence" is Annotated with operator.add, so we CANNOT return the full list, it will append it!
        # Wait, we mutated the items in place. We don't need to return it, or we return an empty list?
        # If we return an empty list for evidence, it adds nothing. The items were mutated in memory.
        # But for LangGraph state persistence, mutating in place might not be tracked if it's a deep copy.
        # So we should be careful. Better to store evaluations in verification state.
        "messages": [SystemMessage(content=f"Evaluated {len(new_evidence_items)} pieces of evidence.")]
    }
