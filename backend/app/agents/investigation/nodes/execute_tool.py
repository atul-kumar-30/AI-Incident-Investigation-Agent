import json
from app.agents.investigation.state import InvestigationState
from app.tools.registry import registry

async def execute_tool(state: InvestigationState) -> dict:
    """Execute the tool requested by the planner."""
    tool_requests = state.get("tool_requests", [])
    
    if not tool_requests:
        return {"errors": ["No tool requested but routed to execute_tool."]}
        
    request = tool_requests[0]
    tool_name = request.get("tool_name")
    tool_input = request.get("tool_input", {})
    
    tool = registry.get_tool(tool_name)
    if not tool:
        error_msg = f"Tool '{tool_name}' not found."
        return {
            "current_step": "execute_tool",
            "errors": [error_msg],
            "tool_results": [{
                "tool_name": tool_name,
                "status": "FAILED",
                "output": {"error": error_msg}
            }]
        }
        
    try:
        # If the tool expects incident_id but it's not explicitly in tool_input,
        # we can optionally inject it. But the LLM should provide it.
        # However, for safety we ensure incident_id is passed if requested.
        if "incident_id" not in tool_input or tool_input["incident_id"] == "auto":
            tool_input["incident_id"] = state.get("incident_id")
            
        result = await tool.execute(**tool_input)
        
        return {
            "current_step": "execute_tool",
            "tool_results": [{
                "tool_name": tool_name,
                "status": "COMPLETED",
                "output": result
            }]
        }
    except Exception as e:
        error_msg = f"Tool '{tool_name}' execution failed: {str(e)}"
        return {
            "current_step": "execute_tool",
            "errors": [error_msg],
            "tool_results": [{
                "tool_name": tool_name,
                "status": "FAILED",
                "output": {"error": error_msg}
            }]
        }
