from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from app.db.session import get_db
from app.models.hypothesis import Hypothesis, HypothesisEvidence
from app.schemas.hypothesis import HypothesisResponse, HypothesisEvidenceResponse

router = APIRouter()

@router.get("/investigations/{run_id}/hypotheses", response_model=List[HypothesisResponse])
async def get_investigation_hypotheses(run_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Hypothesis)
        .where(Hypothesis.investigation_run_id == run_id)
        .options(selectinload(Hypothesis.evidence_mappings).selectinload(HypothesisEvidence.evidence))
        .order_by(Hypothesis.rank.asc())
    )
    hypotheses = result.scalars().all()
    return hypotheses

@router.get("/hypotheses/{hypothesis_id}", response_model=HypothesisResponse)
async def get_hypothesis(hypothesis_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Hypothesis)
        .where(Hypothesis.id == hypothesis_id)
        .options(selectinload(Hypothesis.evidence_mappings).selectinload(HypothesisEvidence.evidence))
    )
    hypothesis = result.scalars().first()
    if not hypothesis:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    return hypothesis

@router.get("/hypotheses/{hypothesis_id}/evidence", response_model=List[HypothesisEvidenceResponse])
async def get_hypothesis_evidence(hypothesis_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(HypothesisEvidence)
        .where(HypothesisEvidence.hypothesis_id == hypothesis_id)
        .options(selectinload(HypothesisEvidence.evidence))
    )
    evidence_mappings = result.scalars().all()
    return evidence_mappings

@router.post("/hypotheses/{hypothesis_id}/verify")
async def verify_hypothesis(hypothesis_id: str, db: AsyncSession = Depends(get_db)):
    from app.services.investigation_service import InvestigationService
    try:
        # In a real app this would be enqueued to a background task
        # But for this implementation, we run it directly
        verification = await InvestigationService.verify_hypothesis(db, hypothesis_id)
        return {"status": "started", "verification_id": verification.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")
