from typing import Type, TypeVar, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
import asyncio
from app.core.config import settings

T = TypeVar("T", bound=BaseModel)

def get_llm():
    """Get the configured LLM instance."""
    if settings.LLM_API_KEY == "MOCK_KEY":
        return None

    if not settings.LLM_API_KEY or settings.LLM_API_KEY == "your_gemini_api_key":
        raise ValueError("Google Gemini API Key is missing. Please configure LLM_API_KEY in backend/.env")

    # We are explicitly using Google Gemini for Phase 2 as per user request.
    return ChatGoogleGenerativeAI(
        model=settings.LLM_MODEL,
        temperature=settings.LLM_TEMPERATURE,
        google_api_key=settings.LLM_API_KEY
    )

class FakeStructuredLLM:
    call_count = 0

    def __init__(self, schema: Type[T]):
        self.schema = schema

    def _get_response(self) -> T:
        FakeStructuredLLM.call_count += 1
        
        if self.schema.__name__ == "EvidenceEvaluation":
            return self.schema.model_construct(
                strength="HIGH",
                relationship="SUPPORTS",
                reasoning="Mock evaluation: This evidence strongly supports the hypothesis."
            )
            
        if self.schema.__name__ == "VerificationDecision":
            if FakeStructuredLLM.call_count % 3 == 1:
                return self.schema.model_construct(
                    reasoning_summary="Need to search logs to verify hypothesis.",
                    next_action="USE_TOOL",
                    tool_name="log_search",
                    tool_input={"incident_id": "auto", "query": "verification search", "limit": 10},
                    selected_requirement="Check logs for errors"
                )
            elif FakeStructuredLLM.call_count % 3 == 2:
                return self.schema.model_construct(
                    reasoning_summary="Need to check code for contradiction.",
                    next_action="USE_TOOL",
                    tool_name="code_search",
                    tool_input={"incident_id": "auto", "query": "verify configuration", "limit": 5},
                    selected_requirement="Check code for contradictory behavior"
                )
            else:
                return self.schema.model_construct(
                    reasoning_summary="Verification complete.",
                    next_action="EVALUATE",
                    tool_name=None,
                    tool_input=None,
                    selected_requirement=""
                )
                
        if self.schema.__name__ == "HypothesisGenerationResult":
            return self.schema.model_construct(
                hypotheses=[
                    {
                        "title": "Database Connection Pool Exhaustion",
                        "description": "The auth-service ran out of available connections in its pool.",
                        "category": "DATABASE",
                        "reasoning_summary": "Logs show timeout errors.",
                        "supporting_evidence_ids": [],
                        "contradicting_evidence_ids": [],
                        "missing_evidence": [{"description": "Check application logs for timeouts"}],
                        "verification_requirements": ["Check db max pool size limit"]
                    }
                ]
            )

        if self.schema.__name__ != "PlannerDecision":
            # For other schemas (e.g. IncidentContextOutput from the tool)
            # return a dummy object safely using construct to bypass validation if needed
            return self.schema.model_construct(
                summary="Dummy context summary",
                signals={
                    "http_status_codes": [502, 500],
                    "endpoints": ["/login"],
                    "components": ["auth-service", "payment-gateway"],
                    "authentication_references": False,
                    "database_references": False,
                    "timeout_references": True,
                    "deployment_related": True,
                    "user_impact_clues": "Checkout/Login failing",
                    "keywords": ["stripe", "timeout", "pool"],
                    "recommended_next_sources": []
                }
            )

        if FakeStructuredLLM.call_count == 1:
            return self.schema.model_construct(
                reasoning_summary="I will analyze the incident context to extract structured signals like HTTP codes and endpoints.",
                next_action="USE_TOOL",
                tool_name="incident_context_analyzer",
                tool_input={"incident_id": "auto"}
            )
        elif FakeStructuredLLM.call_count == 2:
            return self.schema.model_construct(
                reasoning_summary="The incident context identifies /login and HTTP 500 failures, but no runtime evidence is available. Search error logs around the affected endpoint.",
                next_action="USE_TOOL",
                tool_name="log_search",
                tool_input={
                    "incident_id": "auto",
                    "endpoint": "/login",
                    "levels": ["ERROR", "WARN"],
                    "limit": 25
                }
            )
        elif FakeStructuredLLM.call_count == 3:
            return self.schema.model_construct(
                reasoning_summary="The logs contain repeated database timeout signals. A narrower search for database timeout and pool-related messages may reveal correlated events.",
                next_action="USE_TOOL",
                tool_name="log_search",
                tool_input={
                    "incident_id": "auto",
                    "query": "timeout pool",
                    "levels": ["ERROR", "WARN"],
                    "limit": 25
                }
            )
        elif FakeStructuredLLM.call_count == 4:
            return self.schema.model_construct(
                reasoning_summary="Database connection pool timeouts were observed. I will search the codebase to identify where the database connection pool is configured and managed.",
                next_action="USE_TOOL",
                tool_name="code_search",
                tool_input={
                    "incident_id": "auto",
                    "repository_ids": [],
                    "query": "pool timeout connection",
                    "limit": 10
                }
            )
        elif FakeStructuredLLM.call_count == 5:
            return self.schema.model_construct(
                reasoning_summary="I found the connection pool configuration. I should check recent commits to see if this configuration was changed recently.",
                next_action="USE_TOOL",
                tool_name="recent_changes",
                tool_input={
                    "incident_id": "auto",
                    "repository_ids": [],
                    "query": "pool",
                    "max_commits": 5
                }
            )
        elif FakeStructuredLLM.call_count == 6:
            return self.schema.model_construct(
                reasoning_summary="The incident is related to database connection pool timeouts. I should search our operational documentation to see if there is an existing runbook or architectural guidance on pool exhaustion.",
                next_action="USE_TOOL",
                tool_name="docs_search",
                tool_input={
                    "incident_id": "auto",
                    "query": "database connection pool exhaustion timeouts",
                    "document_types": ["RUNBOOK", "ARCHITECTURE"],
                    "top_k": 3
                }
            )
        else:
            return self.schema.model_construct(
                reasoning_summary="Preliminary investigation completed. Log evidence, relevant code, recent repository changes, and operational documentation have been collected.",
                next_action="FINISH",
                tool_name=None,
                tool_input=None
            )

    async def ainvoke(self, prompt: str) -> T:
        await asyncio.sleep(0.1) # Simulate thinking
        return self._get_response()

    def invoke(self, prompt: str) -> T:
        return self._get_response()

def get_structured_llm(schema: Type[T]):
    """Get an LLM bound to a specific Pydantic schema for structured output."""
    llm = get_llm()
    if llm is None:
        return FakeStructuredLLM(schema)
    return llm.with_structured_output(schema)
