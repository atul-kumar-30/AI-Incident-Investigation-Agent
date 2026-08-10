from app.agents.investigation.state import InvestigationState
import app.db.session
from app.models.incident import Incident
from app.models.investigation import InvestigationRun, InvestigationRunStatus

async def initialize(state: InvestigationState) -> dict:
    """Initialize the investigation state by loading incident context."""
    incident_id = state.get("incident_id")
    run_id = state.get("investigation_run_id")

    async with app.db.session.AsyncSessionLocal() as session:
        incident = await session.get(Incident, incident_id)
        if not incident:
            return {"errors": [f"Incident {incident_id} not found."]}

        # Update run status to RUNNING
        run = await session.get(InvestigationRun, run_id)
        if run:
            run.status = InvestigationRunStatus.RUNNING
            session.add(run)
            await session.commit()

        return {
            "incident_title": incident.title,
            "incident_description": incident.description,
            "incident_severity": incident.severity,
            "objective": "Investigate the reported software production incident and determine what information should be collected next.",
            "current_step": "initialize",
            "status": "RUNNING",
            "evidence": [],
            "tool_requests": [],
            "tool_results": [],
            "tool_history": [],
            "iteration_count": 0,
            "max_iterations": 5
        }
