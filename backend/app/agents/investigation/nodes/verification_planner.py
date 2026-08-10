import json
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.investigation.state import InvestigationState
from app.agents.investigation.llm import get_llm

class VerificationDecision(BaseModel):
    reasoning_summary: str = Field(description="Short summary of the verification plan and why this action is taken.")
    next_action: str = Field(description="Must be one of: USE_TOOL, EVALUATE, FINISH_INCONCLUSIVE")
    verification_requirement: str = Field(description="The specific requirement being tested")
    tool_name: str = Field(description="Name of the tool to use (if USE_TOOL). e.g., search_logs, search_code, get_recent_commits, search_documents")
    tool_input: Dict[str, Any] = Field(description="The input arguments for the tool")
    expected_signal: str = Field(description="Evidence that would support the hypothesis")
    contradicting_signal: str = Field(description="Evidence that would contradict the hypothesis")

def verification_planner(state: InvestigationState) -> Dict[str, Any]:
    verification = state.get("verification", {})
    iteration_count = verification.get("iteration_count", 0)
    max_iterations = verification.get("max_iterations", 4)
    budgets = verification.get("tool_budgets", {})
    
    if iteration_count >= max_iterations:
        return {
            "current_step": "finalize_verification",
            "messages": [SystemMessage(content="Verification iteration limit reached.")]
        }
        
    system_prompt = """You are the Verification Planner for an AI Incident Investigation Agent.
Your job is to actively design and plan targeted investigations to test a specific hypothesis.
You MUST search for both supporting and contradicting evidence to prevent confirmation bias.

Available tools:
- search_logs(query, limit, level)
- search_code(query)
- get_recent_commits(query)
- search_documents(query)

Given the hypothesis, the verification requirements, missing evidence, and the tool history, decide the next action.
Allowed actions:
- USE_TOOL: If you have budget and need to gather more evidence for a requirement.
- EVALUATE: If sufficient evidence is gathered, transition to evaluation (note: evidence is evaluated automatically after tool use, so typically use USE_TOOL or FINISH_INCONCLUSIVE).
- FINISH_INCONCLUSIVE: If no more tools can be used, budgets are exhausted, or requirements cannot be tested.

CRITICAL: Do NOT repeat the exact same tool queries that have already been executed.
"""
    
    # Build prompt context
    context = {
        "hypothesis_title": verification.get("hypothesis_title"),
        "hypothesis_description": verification.get("hypothesis_description"),
        "requirements": verification.get("verification_requirements"),
        "missing_evidence": verification.get("missing_evidence"),
        "tool_budgets_remaining": budgets,
        "tool_history": [
            {
                "tool": h.get("tool_name"),
                "input": h.get("input_data"),
                "status": h.get("status")
            } for h in verification.get("tool_history", [])
        ],
        "iteration_count": iteration_count
    }
    
    human_msg = HumanMessage(content=json.dumps(context, indent=2))
    
    from app.agents.investigation.llm import get_structured_llm
    llm = get_structured_llm(VerificationDecision)
    try:
        decision = llm.invoke([SystemMessage(content=system_prompt), human_msg])
    except Exception as e:
        return {
            "current_step": "finalize_verification",
            "messages": [SystemMessage(content=f"Verification planner failed: {str(e)}")]
        }
    
    # Validate action
    if decision.next_action == "USE_TOOL":
        tool_name = decision.tool_name
        # Check budget
        if budgets.get(tool_name, 0) <= 0:
            decision.next_action = "FINISH_INCONCLUSIVE"
            decision.reasoning_summary = f"Budget exhausted for {tool_name}."
        else:
            # Check for duplicate
            is_duplicate = False
            for h in verification.get("tool_history", []):
                if h.get("tool_name") == tool_name and h.get("input_data") == decision.tool_input:
                    is_duplicate = True
                    break
            if is_duplicate:
                decision.next_action = "FINISH_INCONCLUSIVE"
                decision.reasoning_summary = "Duplicate tool call detected. Finishing."
                
    if decision.next_action == "FINISH_INCONCLUSIVE" or decision.next_action == "EVALUATE":
        return {
            "current_step": "finalize_verification",
            "messages": [SystemMessage(content=f"Verification planner decided to finish: {decision.reasoning_summary}")]
        }
        
    # Valid USE_TOOL
    # Format tool requests for execute_tool
    tool_request = {
        "id": f"call_{iteration_count}",
        "name": decision.tool_name,
        "parameters": decision.tool_input
    }
    
    # Update state for next step
    # We must return the updated verification dict
    new_verification = verification.copy()
    new_verification["iteration_count"] = iteration_count + 1
    new_verification["selected_requirement"] = decision.verification_requirement
    new_budgets = budgets.copy()
    if decision.tool_name in new_budgets:
        new_budgets[decision.tool_name] -= 1
    new_verification["tool_budgets"] = new_budgets
    
    # Record the plan in tool_history (PENDING status)
    new_history_item = {
        "step_type": "TOOL_CALL",
        "tool_name": decision.tool_name,
        "objective": decision.verification_requirement,
        "input_data": decision.tool_input,
        "status": "PENDING",
        "expected_signal": decision.expected_signal,
        "contradicting_signal": decision.contradicting_signal
    }
    
    # we use operator.add for tool_history so we return a list of [new_item]
    # Wait, in VerificationState we have tool_history: Annotated[List, add]
    # But we can't easily return just the nested update.
    # We must return the entire verification dict to merge. But dict merge with Annotated fields inside nested dicts might not work out of the box in langgraph unless specified.
    # Actually, in TypedDict, if we update a nested dict, the whole dict is overwritten unless we specify a custom reducer for the dict itself.
    # Wait, if `verification` is a single key in `InvestigationState` without a reducer, overwriting it replaces it entirely!
    # Let me check state.py. `verification: VerificationState`. No reducer. So returning `{"verification": new_verification}` replaces it completely.
    # So we must append to `tool_history` explicitly here.
    
    new_verification["tool_history"] = verification.get("tool_history", []) + [new_history_item]
    
    return {
        "current_step": "execute_tool",
        "tool_requests": [tool_request],
        "verification": new_verification,
        "messages": [SystemMessage(content=f"Verification Plan: {decision.reasoning_summary}\nExecuting: {decision.tool_name}")]
    }
