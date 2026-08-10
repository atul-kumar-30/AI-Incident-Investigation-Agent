from app.agents.investigation.state import InvestigationState

def tool_router(state: InvestigationState) -> str:
    """Route based on the planner's decision."""
    iteration_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 5)
    
    if iteration_count >= max_iterations:
        return "finalize"
        
    tool_requests = state.get("tool_requests", [])
    if tool_requests:
        return "execute_tool"
    return "finalize"
