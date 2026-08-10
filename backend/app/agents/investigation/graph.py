from langgraph.graph import StateGraph, START, END
from app.agents.investigation.state import InvestigationState
from app.agents.investigation.nodes.initialize import initialize
from app.agents.investigation.nodes.planner import planner
from app.agents.investigation.nodes.tool_router import tool_router
from app.agents.investigation.nodes.execute_tool import execute_tool
from app.agents.investigation.nodes.record_evidence import record_evidence
from app.agents.investigation.nodes.synthesize_evidence import synthesize_evidence
from app.agents.investigation.nodes.generate_hypotheses import generate_hypotheses
from app.agents.investigation.nodes.map_evidence import map_evidence
from app.agents.investigation.nodes.rank_hypotheses import rank_hypotheses
from app.agents.investigation.nodes.finalize import finalize
from app.agents.investigation.nodes.select_hypothesis_for_verification import select_hypothesis_for_verification
from app.agents.investigation.nodes.verification_planner import verification_planner
from app.agents.investigation.nodes.evaluate_verification_evidence import evaluate_verification_evidence
from app.agents.investigation.nodes.finalize_verification import finalize_verification

def route_after_record_evidence(state: InvestigationState) -> str:
    verification = state.get("verification", {})
    if verification and verification.get("status") == "RUNNING":
        return "evaluate_verification_evidence"
    return "planner"

def create_investigation_graph():
    workflow = StateGraph(InvestigationState)

    # Add nodes
    workflow.add_node("initialize", initialize)
    workflow.add_node("planner", planner)
    workflow.add_node("execute_tool", execute_tool)
    workflow.add_node("record_evidence", record_evidence)
    workflow.add_node("synthesize_evidence", synthesize_evidence)
    workflow.add_node("generate_hypotheses", generate_hypotheses)
    workflow.add_node("map_evidence", map_evidence)
    workflow.add_node("rank_hypotheses", rank_hypotheses)
    
    # Phase 7 nodes
    workflow.add_node("select_hypothesis_for_verification", select_hypothesis_for_verification)
    workflow.add_node("verification_planner", verification_planner)
    workflow.add_node("evaluate_verification_evidence", evaluate_verification_evidence)
    workflow.add_node("finalize_verification", finalize_verification)
    
    workflow.add_node("finalize", finalize)

    # Add edges
    workflow.add_edge(START, "initialize")
    workflow.add_edge("initialize", "planner")
    
    # Conditional routing from planner
    workflow.add_conditional_edges(
        "planner",
        tool_router,
        {
            "execute_tool": "execute_tool",
            "finalize": "synthesize_evidence" # Modified for Phase 6
        }
    )
    
    # After tool execution, record evidence
    workflow.add_edge("execute_tool", "record_evidence")
    
    # Conditional routing from record_evidence
    workflow.add_conditional_edges(
        "record_evidence",
        route_after_record_evidence,
        {
            "planner": "planner",
            "evaluate_verification_evidence": "evaluate_verification_evidence"
        }
    )
    
    # Phase 6 linear flow
    workflow.add_edge("synthesize_evidence", "generate_hypotheses")
    workflow.add_edge("generate_hypotheses", "map_evidence")
    workflow.add_edge("map_evidence", "rank_hypotheses")
    
    # Transition to Phase 7
    workflow.add_edge("rank_hypotheses", "select_hypothesis_for_verification")
    
    # Verification routing
    workflow.add_conditional_edges(
        "select_hypothesis_for_verification",
        lambda state: state.get("current_step", "verification_planner"),
        {
            "verification_planner": "verification_planner",
            "finalize": "finalize"
        }
    )
    
    workflow.add_conditional_edges(
        "verification_planner",
        lambda state: state.get("current_step", "execute_tool"),
        {
            "execute_tool": "execute_tool",
            "finalize_verification": "finalize_verification"
        }
    )
    
    workflow.add_edge("evaluate_verification_evidence", "verification_planner")
    workflow.add_edge("finalize_verification", "select_hypothesis_for_verification")
    
    workflow.add_edge("finalize", END)

    # Compile the graph
    app = workflow.compile()
    return app

investigation_graph = create_investigation_graph()
