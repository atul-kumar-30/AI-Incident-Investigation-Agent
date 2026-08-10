from datetime import datetime, timezone
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from app.models.investigation import (
    InvestigationRun, InvestigationRunStatus, 
    InvestigationStep, StepType, StepStatus, Evidence
)
from app.models.incident import Incident, incident_repositories
from app.models.repository import Repository
from app.models.hypothesis import (
    Hypothesis, HypothesisEvidence, HypothesisVerification, VerificationStep,
    HypothesisVerificationStatus, VerificationStepType
)
from app.agents.investigation.graph import investigation_graph
from app.agents.investigation.state import InvestigationState

class InvestigationService:
    @staticmethod
    async def start_investigation(db: AsyncSession, incident_id: str) -> InvestigationRun:
        incident = await db.get(Incident, incident_id)
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")

        # Create new run
        run = InvestigationRun(
            incident_id=incident_id,
            status=InvestigationRunStatus.PENDING,
            started_at=datetime.now(timezone.utc)
        )
        db.add(run)
        await db.commit()
        await db.refresh(run)

        # Get available repositories
        repo_result = await db.execute(
            select(Repository).join(
                incident_repositories, 
                incident_repositories.c.repository_id == Repository.id
            ).where(incident_repositories.c.incident_id == incident_id)
        )
        repos = repo_result.scalars().all()
        repo_list = [{"id": r.id, "name": r.name, "source_location": r.source_location} for r in repos]

        # Kick off graph
        initial_state = {
            "incident_id": incident_id,
            "investigation_run_id": run.id,
            "incident_title": "",
            "incident_description": "",
            "incident_severity": "",
            "objective": "",
            "plan": "",
            "current_step": "start",
            "tool_requests": [],
            "tool_results": [],
            "evidence": [],
            "messages": [],
            "errors": [],
            "status": "PENDING",
            "tool_history": [],
            "iteration_count": 0,
            "max_iterations": 7,
            "tool_budget": {
                "incident_context_analyzer": 1,
                "log_search": 3,
                "code_search": 3,
                "recent_changes": 2
            },
            "available_repositories": repo_list
        }
        
        # Kick off graph
        try:
            await InvestigationService._execute_graph(db, run, initial_state)
        except Exception as e:
            # If it fails synchronously, we still want to return the run but we should refresh it
            pass
            
        await db.refresh(run)
        return run

    @staticmethod
    async def verify_hypothesis(db: AsyncSession, hypothesis_id: str) -> HypothesisVerification:
        # Get hypothesis
        stmt = select(Hypothesis).where(Hypothesis.id == hypothesis_id)
        result = await db.execute(stmt)
        hypothesis = result.scalars().first()
        if not hypothesis:
            raise ValueError("Hypothesis not found")
            
        run = await db.get(InvestigationRun, hypothesis.investigation_run_id)
        
        # Check for existing verification
        stmt = select(HypothesisVerification).where(
            HypothesisVerification.hypothesis_id == hypothesis_id,
            HypothesisVerification.status.in_([HypothesisVerificationStatus.PENDING, HypothesisVerificationStatus.RUNNING])
        )
        existing = await db.execute(stmt)
        if existing.scalars().first():
            raise ValueError("Verification already running for this hypothesis")
            
        # Reconstruct state from DB to run verification subgraph
        # We need evidence, existing mappings, hypotheses list
        evidence_records = await InvestigationService.get_evidence(db, run.id)
        evidence_state = [{"id": e.id, "source_type": e.source_type, "source_name": e.source_name, "content": e.content, "metadata": e.metadata_} for e in evidence_records]
        
        hyp_stmt = select(Hypothesis).where(Hypothesis.investigation_run_id == run.id)
        hyp_result = await db.execute(hyp_stmt)
        all_hyps = hyp_result.scalars().all()
        hyp_state = [{
            "id": h.id, "temp_id": h.id, "title": h.title, "description": h.description, 
            "category": h.category, "status": h.status, "rank": h.rank, 
            "preliminary_score": h.score, "missing_evidence": h.missing_evidence,
            "verification_requirements": h.verification_requirements
        } for h in all_hyps]
        
        map_stmt = select(HypothesisEvidence).join(Hypothesis).where(Hypothesis.investigation_run_id == run.id)
        map_result = await db.execute(map_stmt)
        all_maps = map_result.scalars().all()
        map_state = [{"hypothesis_id": m.hypothesis_id, "hypothesis_temp_id": m.hypothesis_id, "evidence_id": m.evidence_id, "relationship": m.relationship, "strength": m.strength, "reason": m.reason} for m in all_maps]
        
        state = {
            "incident_id": run.incident_id,
            "investigation_run_id": run.id,
            "current_step": "select_hypothesis_for_verification",
            "evidence": evidence_state,
            "hypotheses": hyp_state,
            "hypothesis_evidence_mappings": map_state,
            "target_hypothesis_id": hypothesis_id,
            "completed_verifications": []
        }
        
        # Execute graph from verification entry point
        # The graph will run select_hypothesis_for_verification and verify this one hypothesis
        await InvestigationService._execute_graph(db, run, state)
        
        # Get the completed verification
        v_stmt = select(HypothesisVerification).where(HypothesisVerification.hypothesis_id == hypothesis_id).order_by(HypothesisVerification.created_at.desc())
        v_result = await db.execute(v_stmt)
        return v_result.scalars().first()

    @staticmethod
    async def _execute_graph(db: AsyncSession, run: InvestigationRun, state: dict):
        try:
            step_number = 1
            # Fetch latest step number
            stmt = select(InvestigationStep).where(InvestigationStep.investigation_run_id == run.id).order_by(InvestigationStep.step_number.desc())
            latest_step = (await db.execute(stmt)).scalars().first()
            if latest_step:
                step_number = latest_step.step_number + 1

            current_verification_model = None

            async for output in investigation_graph.astream(state):
                for node_name, state_update in output.items():
                    # Record the step
                    step_type = StepType.SYSTEM
                    if node_name == "planner":
                        step_type = StepType.PLANNING
                    elif node_name == "execute_tool":
                        step_type = StepType.TOOL_CALL
                    elif node_name == "record_evidence":
                        step_type = StepType.TOOL_RESULT
                        
                    from langchain_core.messages import BaseMessage
                    safe_update = {}
                    for k, v in state_update.items():
                        if k == "messages":
                            safe_update[k] = [m.content if isinstance(m, BaseMessage) else str(m) for m in v] if hasattr(v, '__iter__') else str(v)
                        else:
                            safe_update[k] = v

                    step = InvestigationStep(
                        investigation_run_id=run.id,
                        step_number=step_number,
                        node_name=node_name,
                        step_type=step_type,
                        status=StepStatus.COMPLETED,
                        input_data={},  
                        output_data={"update": safe_update},
                        started_at=datetime.now(timezone.utc),
                        completed_at=datetime.now(timezone.utc)
                    )
                    db.add(step)
                    
                    # Persist evidence
                    if "evidence" in state_update and state_update["evidence"]:
                        # only persist new evidence (not yet in DB)
                        existing_eids = {e.id for e in await InvestigationService.get_evidence(db, run.id)}
                        for e in state_update["evidence"]:
                            if e.get("id") not in existing_eids:
                                evidence_record = Evidence(
                                    id=e.get("id"),
                                    investigation_run_id=run.id,
                                    source_type=e.get("source_type"),
                                    source_name=e.get("source_name"),
                                    content=e.get("content"),
                                    metadata_=e.get("metadata")
                                )
                                db.add(evidence_record)
                                existing_eids.add(e.get("id"))
                                
                    # Sync Verification State
                    verification_state = state_update.get("verification")
                    if verification_state:
                        vid = verification_state.get("verification_id")
                        if vid:
                            v_model = await db.get(HypothesisVerification, vid)
                            if not v_model:
                                v_model = HypothesisVerification(
                                    id=vid,
                                    hypothesis_id=verification_state.get("hypothesis_id"),
                                    investigation_run_id=run.id,
                                    status=HypothesisVerificationStatus(verification_state.get("status", "PENDING")),
                                    initial_score=verification_state.get("current_score"),
                                    started_at=datetime.now(timezone.utc)
                                )
                                db.add(v_model)
                            else:
                                v_model.status = HypothesisVerificationStatus(verification_state.get("status", "RUNNING"))
                                v_model.support_delta = verification_state.get("support_delta", 0.0)
                                v_model.contradiction_delta = verification_state.get("contradiction_delta", 0.0)
                                v_model.summary = verification_state.get("summary")
                                if verification_state.get("status") == "COMPLETED":
                                    v_model.completed_at = datetime.now(timezone.utc)
                            current_verification_model = v_model
                            
                            # Sync tool history to verification steps
                            for idx, t_hist in enumerate(verification_state.get("tool_history", [])):
                                # Ensure it doesn't already exist
                                v_step_id = f"{vid}_step_{idx}"
                                v_step = await db.get(VerificationStep, v_step_id)
                                if not v_step:
                                    v_step = VerificationStep(
                                        id=v_step_id,
                                        verification_id=vid,
                                        step_number=idx,
                                        step_type=VerificationStepType.TOOL_CALL,
                                        status=t_hist.get("status", "PENDING"),
                                        tool_name=t_hist.get("tool_name"),
                                        objective=t_hist.get("objective"),
                                        input_data=t_hist.get("input_data"),
                                        started_at=datetime.now(timezone.utc)
                                    )
                                    db.add(v_step)
                                else:
                                    v_step.status = t_hist.get("status")
                                    if v_step.status == "COMPLETED" and not v_step.completed_at:
                                        v_step.completed_at = datetime.now(timezone.utc)
                                        
                    if node_name == "rank_hypotheses":
                        hypotheses_data = state_update.get("hypotheses", [])
                        # We might need to look in the merged state for mappings if not in state_update
                        # Actually we can just trust state_update if it contains mappings.
                        mappings_data = state_update.get("hypothesis_evidence_mappings", [])
                        
                        temp_to_id = {}
                        
                        for h_data in hypotheses_data:
                            h_id = h_data.get("id")
                            if h_id:
                                h = await db.get(Hypothesis, h_id)
                                if h:
                                    h.status = h_data.get("status", h.status)
                                    h.rank = h_data.get("rank")
                                    h.score = h_data.get("preliminary_score")
                            else:
                                # New hypothesis
                                h = Hypothesis(
                                    investigation_run_id=run.id,
                                    title=h_data.get("title"),
                                    description=h_data.get("description"),
                                    category=h_data.get("category"),
                                    status=h_data.get("status", "PROPOSED"),
                                    rank=h_data.get("rank"),
                                    score=h_data.get("preliminary_score"),
                                    generation_source="LLM",
                                    reasoning_summary=h_data.get("reasoning_summary"),
                                    missing_evidence=h_data.get("missing_evidence"),
                                    verification_requirements=h_data.get("verification_requirements")
                                )
                                db.add(h)
                                await db.flush()
                                h_data["id"] = h.id
                                
                            temp_to_id[h_data.get("temp_id")] = h.id
                            
                        # Delete existing mappings for this run and recreate them to ensure sync
                        # Or better, just upsert.
                        if mappings_data:
                            # clear old
                            await db.execute(delete(HypothesisEvidence).where(
                                HypothesisEvidence.hypothesis_id.in_(
                                    select(Hypothesis.id).where(Hypothesis.investigation_run_id == run.id)
                                )
                            ))
                            for m_data in mappings_data:
                                real_h_id = m_data.get("hypothesis_id") or temp_to_id.get(m_data.get("hypothesis_temp_id"))
                                if real_h_id:
                                    he = HypothesisEvidence(
                                        hypothesis_id=real_h_id,
                                        evidence_id=m_data.get("evidence_id"),
                                        relationship=m_data.get("relationship"),
                                        strength=m_data.get("strength"),
                                        reason=m_data.get("reason"),
                                        origin=m_data.get("origin", "INITIAL")
                                    )
                                    # Link to verification if origin is VERIFICATION
                                    if he.origin == "VERIFICATION" and current_verification_model:
                                        he.verification_id = current_verification_model.id
                                    db.add(he)
                                    
                        # Update final_score on current verification if any
                        if current_verification_model and current_verification_model.status == HypothesisVerificationStatus.COMPLETED:
                            for h_data in hypotheses_data:
                                if h_data.get("id") == current_verification_model.hypothesis_id or h_data.get("temp_id") == current_verification_model.hypothesis_id:
                                    current_verification_model.final_score = h_data.get("preliminary_score")
                            
                    step_number += 1
                    
                    if node_name == "finalize":
                        run.status = InvestigationRunStatus(state_update.get("status", "COMPLETED"))
                        run.summary = state_update.get("summary")
                        run.completed_at = datetime.now(timezone.utc)
                        db.add(run)

            await db.commit()
            
        except Exception as e:
            run.status = InvestigationRunStatus.FAILED
            run.summary = f"Execution failed: {str(e)}"
            run.completed_at = datetime.now(timezone.utc)
            db.add(run)
            
            step = InvestigationStep(
                investigation_run_id=run.id,
                step_number=0,
                node_name="system",
                step_type=StepType.SYSTEM,
                status=StepStatus.FAILED,
                output_data={"error": str(e)},
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc)
            )
            db.add(step)
            await db.commit()
            
            if current_verification_model:
                current_verification_model.status = HypothesisVerificationStatus.FAILED
                await db.commit()
                
            raise e

    @staticmethod
    async def get_run(db: AsyncSession, run_id: str) -> InvestigationRun:
        return await db.get(InvestigationRun, run_id)
        
    @staticmethod
    async def get_steps(db: AsyncSession, run_id: str) -> List[InvestigationStep]:
        stmt = select(InvestigationStep).where(InvestigationStep.investigation_run_id == run_id).order_by(InvestigationStep.step_number.asc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_evidence(db: AsyncSession, run_id: str) -> List[Evidence]:
        stmt = select(Evidence).where(Evidence.investigation_run_id == run_id).order_by(Evidence.created_at.asc())
        result = await db.execute(stmt)
        return list(result.scalars().all())
