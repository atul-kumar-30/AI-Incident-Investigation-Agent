import json
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from app.agents.investigation.state import InvestigationState
from app.agents.investigation.llm import get_structured_llm
from app.models.hypothesis import HypothesisCategory

class HypothesisCandidate(BaseModel):
    title: str = Field(description="Short descriptive title of the hypothesis", max_length=100)
    description: str = Field(description="Detailed explanation of the proposed mechanism")
    category: HypothesisCategory = Field(description="Category of the hypothesis")
    reasoning_summary: str = Field(description="Concise safe explanation of why the evidence supports this hypothesis without revealing hidden internal reasoning.")
    supporting_evidence_ids: List[str] = Field(description="List of exact evidence IDs that support this hypothesis")
    contradicting_evidence_ids: List[str] = Field(description="List of exact evidence IDs that contradict this hypothesis")
    missing_evidence: List[Dict[str, str]] = Field(description="List of missing evidence requirements, each containing 'description' and optionally 'preferred_source'")
    verification_requirements: List[str] = Field(description="Explicit requirements for what needs to be established in Phase 7 to verify this hypothesis")

class HypothesisGenerationResult(BaseModel):
    hypotheses: List[HypothesisCandidate] = Field(description="List of distinct, plausible candidate hypotheses (target 3-5)")

def normalize_title(title: str) -> str:
    """Helper to deterministically normalize a title for duplication checks"""
    import re
    return re.sub(r'[^a-z0-9]+', ' ', title.lower()).strip()

def deduplicate_hypotheses(hypotheses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deterministically deduplicate hypotheses based on normalized title, category, and shared evidence"""
    unique = []
    seen_keys = set()
    
    for h in hypotheses:
        norm_title = normalize_title(h["title"])
        category = h["category"]
        
        # Simple heuristic key: first 3 words of normalized title + category
        words = norm_title.split()[:3]
        key = f"{category}_{'_'.join(words)}"
        
        if key not in seen_keys:
            seen_keys.add(key)
            unique.append(h)
    
    return unique

def validate_evidence_ids(hypothesis: Dict[str, Any], valid_ids: set) -> Dict[str, Any]:
    """Ensure all evidence IDs exist in the current investigation run"""
    hypothesis["supporting_evidence_ids"] = [
        eid for eid in hypothesis.get("supporting_evidence_ids", []) if eid in valid_ids
    ]
    hypothesis["contradicting_evidence_ids"] = [
        eid for eid in hypothesis.get("contradicting_evidence_ids", []) if eid in valid_ids
    ]
    return hypothesis

def generate_hypotheses(state: InvestigationState) -> Dict[str, Any]:
    """
    LLM-powered node to generate multiple plausible, testable candidate explanations based on evidence.
    """
    synthesis = state.get("evidence_synthesis", {})
    valid_ids = set(synthesis.get("all_evidence_ids", []))
    
    prompt = f"""
You are an expert site reliability engineer investigating an incident.
Based on the following evidence synthesis, generate multiple (3-5) distinct plausible, testable candidate hypotheses for the incident.
Do NOT simply choose one and declare it the root cause.
Do NOT invent evidence or hallucinate evidence IDs. Only use the IDs provided.
Distinguish facts from hypotheses.
Include evidence gaps and contradictory evidence when relevant.
Avoid duplicate explanations (e.g. "pool size reduced" and "smaller connection pool" are the same).

Incident: {synthesis.get("incident")}
Runtime Signals: {json.dumps(synthesis.get("runtime_signals", []))}
Code Findings: {json.dumps(synthesis.get("code_findings", []))}
Change Findings: {json.dumps(synthesis.get("change_findings", []))}
Documentation Findings: {json.dumps(synthesis.get("documentation_findings", []))}
Timeline: {json.dumps(synthesis.get("timeline", []))}
Known Gaps: {json.dumps(synthesis.get("known_gaps", []))}

Available Evidence IDs: {list(valid_ids)}
"""

    llm = get_structured_llm(HypothesisGenerationResult)
    
    # Bounded retries
    max_retries = 2
    result = None
    
    for attempt in range(max_retries):
        try:
            result = llm.invoke([
                SystemMessage(content="You generate evidence-grounded hypotheses."),
                HumanMessage(content=prompt)
            ])
            break
        except Exception as e:
            if attempt == max_retries - 1:
                return {
                    "errors": [f"Hypothesis generation failed after {max_retries} attempts: {str(e)}"],
                    "current_step": "generate_hypotheses"
                }
    
    if not result or not result.hypotheses:
        return {
            "messages": [HumanMessage(content="Current evidence is insufficient to generate strongly supported hypotheses.")],
            "hypotheses": [],
            "current_step": "generate_hypotheses"
        }
        
    raw_hypotheses = [h.dict() if hasattr(h, 'dict') else dict(h) for h in result.hypotheses]
    
    # Quality Guardrails: Deduplicate and Validate IDs
    validated = [validate_evidence_ids(h, valid_ids) for h in raw_hypotheses]
    deduplicated = deduplicate_hypotheses(validated)
    
    # Filter out empty evidence lists if they have no support at all (optional, but good for quality)
    final_hypotheses = [
        h for h in deduplicated 
        if h.get("supporting_evidence_ids") or h.get("missing_evidence")
    ]

    return {
        "hypotheses": final_hypotheses,
        "current_step": "generate_hypotheses",
        "messages": [HumanMessage(content=f"Generated {len(final_hypotheses)} hypotheses.")]
    }
