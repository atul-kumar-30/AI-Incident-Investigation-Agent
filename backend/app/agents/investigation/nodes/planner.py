import json
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from app.agents.investigation.state import InvestigationState
from app.agents.investigation.llm import get_structured_llm
from app.agents.investigation.prompts.planner import PLANNER_SYSTEM_PROMPT
from app.tools.registry import registry

class PlannerDecision(BaseModel):
    reasoning_summary: str = Field(description="A concise, safe explanation of why this action was selected.")
    next_action: str = Field(description="Must be either 'USE_TOOL' or 'FINISH_EVIDENCE_COLLECTION'.")
    tool_name: Optional[str] = Field(description="The name of the tool to use (if next_action is USE_TOOL).", default=None)
    tool_input: Optional[Dict[str, Any]] = Field(description="The JSON arguments for the tool.", default=None)

async def planner(state: InvestigationState) -> dict:
    """Planner node to decide the next investigation action."""
    
    # Prepare tools context
    tools = registry.get_all_tools()
    tools_context = ""
    for name, tool in tools.items():
        tools_context += f"- **{name}**: {tool.description}\n  Input Schema: {json.dumps(tool.input_schema)}\n"
        
    system_prompt = PLANNER_SYSTEM_PROMPT.format(tools_context=tools_context)
    
    # Prepare incident and evidence context
    content = f"""
    # Incident
    Title: {state.get('incident_title')}
    Severity: {state.get('incident_severity')}
    Description: {state.get('incident_description')}
    
    # Evidence Collected
    """
    evidence = state.get("evidence", [])
    if evidence:
        for e in evidence:
            content += f"\n- Source [{e.get('source_type')}]: {e.get('source_name')}\n  Content: {e.get('content')}\n"
    else:
        content += "\nNo evidence collected yet."
        
    iteration_count = state.get("iteration_count", 0) + 1
    max_iterations = state.get("max_iterations", 7)
    
    content += f"\n\n# Investigation State\nIteration: {iteration_count} of {max_iterations}"
    
    # Tool budget
    tool_budget = state.get("tool_budget", {})
    if tool_budget:
        content += "\n\n# Remaining Tool Budget"
        for t, count in tool_budget.items():
            content += f"\n- {t}: {count} calls remaining"
            
    # Repositories
    repos = state.get("available_repositories", [])
    if repos:
        content += "\n\n# Available Repositories"
        for r in repos:
            content += f"\n- ID: {r.get('id')}, Name: {r.get('name')}"
    else:
        content += "\n\n# Available Repositories\nNone. Do NOT use code_search or recent_changes."
        
    # Documents
    content += f"\n\n# Environment Availability"
    content += f"\n- Logs: {'Available' if state.get('logs_available') else 'Unavailable'}"
    content += f"\n- Documents: {'Available' if state.get('documents_available') else 'Unavailable'}"
    content += f"\n- Runbooks: {'Available' if state.get('runbooks_available') else 'Unavailable'}"
    
    if not state.get('documents_available') and not state.get('runbooks_available'):
        content += "\nDo NOT use docs_search tool."
    
    tool_history = state.get("tool_history", [])
    if tool_history:
        content += "\n\n# Previous Tool Requests"
        for h in tool_history:
            content += f"\n- {h.get('tool_name')} with input: {json.dumps(h.get('tool_input', {}))}"
        content += "\nIMPORTANT: Do not repeat identical tool requests that were already made."
        
    prompt = f"{system_prompt}\n\n{content}"
    
    llm = get_structured_llm(PlannerDecision)
    decision: PlannerDecision = await llm.ainvoke(prompt)
    
    updates = {
        "current_step": "planner",
        "plan": decision.reasoning_summary,
    }
    
    if decision.next_action == "USE_TOOL" and decision.tool_name:
        # Check for duplicate
        is_duplicate = False
        tool_input = decision.tool_input or {}
        for h in tool_history:
            if h.get("tool_name") == decision.tool_name and h.get("tool_input") == tool_input:
                is_duplicate = True
                break
                
        if is_duplicate:
            updates["plan"] = f"{decision.reasoning_summary}\n\nSystem: Requested duplicate tool call {decision.tool_name}. Forcing FINISH_EVIDENCE_COLLECTION to prevent infinite loop."
            updates["tool_requests"] = []
            updates["current_step"] = "planner"
            # Return FINISH condition
        else:
            # Enforce tool budget
            tool_budget = state.get("tool_budget", {})
            current_budget = tool_budget.get(decision.tool_name, 999)
            if current_budget <= 0:
                updates["plan"] = f"{decision.reasoning_summary}\n\nSystem: Tool budget for {decision.tool_name} exhausted. Forcing FINISH_EVIDENCE_COLLECTION."
                updates["tool_requests"] = []
                updates["current_step"] = "planner"
            else:
                updates["tool_requests"] = [{
                    "tool_name": decision.tool_name,
                    "tool_input": tool_input
                }]
                updates["tool_history"] = [{
                    "tool_name": decision.tool_name,
                    "tool_input": tool_input,
                    "iteration": iteration_count
                }]
                
                # Decrement budget
                if decision.tool_name in tool_budget:
                    new_budget = dict(tool_budget)
                    new_budget[decision.tool_name] -= 1
                    updates["tool_budget"] = new_budget
    else:
        updates["tool_requests"] = []
        
    updates["iteration_count"] = iteration_count
        
    return updates
