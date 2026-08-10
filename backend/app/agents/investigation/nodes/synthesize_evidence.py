from typing import Dict, Any, List
from langchain_core.messages import HumanMessage
from app.agents.investigation.state import InvestigationState

def synthesize_evidence(state: InvestigationState) -> Dict[str, Any]:
    """
    Synthesizes collected evidence into a compact structured format for hypothesis generation.
    Groups evidence by source type and extracts key findings, keeping evidence IDs intact.
    """
    evidence_list = state.get("evidence", [])
    
    synthesis = {
        "incident": {
            "title": state.get("incident_title", ""),
            "severity": state.get("incident_severity", "UNKNOWN"),
        },
        "runtime_signals": [],
        "code_findings": [],
        "change_findings": [],
        "documentation_findings": [],
        "timeline": [],
        "known_gaps": [],
        "all_evidence_ids": [ev["id"] for ev in evidence_list if "id" in ev]
    }
    
    # Simple grouping
    for ev in evidence_list:
        source_type = ev.get("source_type")
        ev_id = ev.get("id")
        content = ev.get("content", "")
        
        # A lightweight representation of evidence for synthesis
        finding = {
            "evidence_ids": [ev_id],
            "summary": content[:500] + "..." if len(content) > 500 else content
        }
        
        if source_type in ("LOG", "METRIC", "TRACE"):
            synthesis["runtime_signals"].append(finding)
        elif source_type == "CODE":
            synthesis["code_findings"].append(finding)
        elif source_type == "GIT_CHANGE":
            synthesis["change_findings"].append(finding)
        elif source_type == "DOCUMENT":
            synthesis["documentation_findings"].append(finding)
        else:
            synthesis["timeline"].append(finding)
            
    # Add to state and return
    return {
        "evidence_synthesis": synthesis,
        "current_step": "synthesize_evidence",
        "messages": [HumanMessage(content="Evidence synthesized successfully.")]
    }
