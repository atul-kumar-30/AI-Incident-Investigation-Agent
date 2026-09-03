from app.agents.investigation.state import InvestigationState

def tool_router(state: InvestigationState) -> str:
    """Route based on the planner's decision."""
    tool_requests = state.get("tool_requests", [])
    if not tool_requests:
        return "finalize"

    iteration_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 7)
    
    if iteration_count > max_iterations:
        return "finalize"
        
    return "execute_tool"
