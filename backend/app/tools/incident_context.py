from typing import Any, Dict, List
from pydantic import BaseModel
from app.tools.base import BaseTool
import app.db.session
from app.models.incident import Incident
from app.agents.investigation.llm import get_structured_llm

class IncidentSignals(BaseModel):
    http_status_codes: List[int]
    endpoints: List[str]
    components: List[str]
    authentication_references: bool
    database_references: bool
    timeout_references: bool
    deployment_related: bool
    user_impact_clues: str
    keywords: List[str]
    recommended_next_sources: List[str]

class IncidentContextOutput(BaseModel):
    summary: str
    signals: IncidentSignals

class IncidentContextAnalyzer(BaseTool):
    name = "incident_context_analyzer"
    description = "Analyzes the incident description to extract structured signals like HTTP codes, endpoints, and deployment clues."
    input_schema = {
        "type": "object",
        "properties": {
            "incident_id": {"type": "string", "description": "The ID of the incident to analyze"}
        },
        "required": ["incident_id"]
    }

    async def execute(self, incident_id: str, **kwargs) -> Dict[str, Any]:
        async with app.db.session.AsyncSessionLocal() as session:
            incident = await session.get(Incident, incident_id)
            if not incident:
                raise ValueError(f"Incident {incident_id} not found")

            # Prepare content for LLM
            content = f"Title: {incident.title}\nDescription: {incident.description}\nSeverity: {incident.severity}"

            # Use LLM to extract structured signals
            llm = get_structured_llm(IncidentContextOutput)
            prompt = f"Analyze the following incident report and extract structured signals according to the schema.\n\n{content}"
            
            result: IncidentContextOutput = await llm.ainvoke(prompt)
            
            return result.model_dump()
