from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from app.db.session import get_db
from app.models.hypothesis import HypothesisVerification, VerificationStep

router = APIRouter()

@router.get("/hypotheses/{hypothesis_id}/verifications")
async def get_hypothesis_verifications(hypothesis_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(HypothesisVerification)
        .where(HypothesisVerification.hypothesis_id == hypothesis_id)
        .order_by(HypothesisVerification.created_at.desc())
    )
    return result.scalars().all()

@router.get("/verifications/{verification_id}")
async def get_verification(verification_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(HypothesisVerification)
        .where(HypothesisVerification.id == verification_id)
    )
    verification = result.scalars().first()
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    return verification

@router.get("/verifications/{verification_id}/steps")
async def get_verification_steps(verification_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(VerificationStep)
        .where(VerificationStep.verification_id == verification_id)
        .order_by(VerificationStep.step_number.asc())
    )
    return result.scalars().all()
