from typing import TypedDict, List, Dict, Any, Optional
import operator
from typing import Annotated

class VerificationState(TypedDict, total=False):
    verification_id: str
    hypothesis_id: str
    hypothesis_title: str
    hypothesis_description: str
    hypothesis_category: str
    
    current_score: float
    verification_requirements: List[Any]
    missing_evidence: List[Any]
    selected_requirement: str
    
    tool_history: Annotated[List[Dict[str, Any]], operator.add]
    new_evidence_ids: List[str]
    supporting_evidence_ids: Annotated[List[str], operator.add]
    contradicting_evidence_ids: Annotated[List[str], operator.add]
    
    iteration_count: int
    max_iterations: int
    tool_budgets: Dict[str, int]
    
    status: str
    errors: Annotated[List[str], operator.add]

class InvestigationState(TypedDict):
    incident_id: str
    investigation_run_id: str
    
    incident_title: str
    incident_description: str
    incident_severity: str
    
    objective: str
    plan: str
    
    current_step: str
    
    tool_requests: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    tool_history: Annotated[List[Dict[str, Any]], operator.add]
    
    iteration_count: int
    max_iterations: int
    
    # Environment availability
    logs_available: bool
    repositories_available: bool
    documents_available: bool
    runbooks_available: bool
    
    tool_budget: Dict[str, int]
    available_repositories: List[Dict[str, Any]]
    
    # Annotated with operator.add to allow appending to the list across nodes
    evidence: Annotated[List[Dict[str, Any]], operator.add]
    
    # Phase 6
    evidence_synthesis: Dict[str, Any]
    hypotheses: List[Dict[str, Any]]
    hypothesis_evidence_mappings: List[Dict[str, Any]]
    
    # Phase 7
    verification: VerificationState
    completed_verifications: Annotated[List[str], operator.add]
    target_hypothesis_id: Optional[str]
    
    messages: Annotated[List[Dict[str, Any]], operator.add]
    errors: Annotated[List[str], operator.add]
    
    status: str
