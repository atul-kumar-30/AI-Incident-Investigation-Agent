from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.schemas.investigation import (
    InvestigationRunResponse, InvestigationStepResponse, EvidenceResponse
)
from app.services.investigation_service import InvestigationService

router = APIRouter()

@router.post("/incidents/{incident_id}/investigations", response_model=InvestigationRunResponse, status_code=status.HTTP_201_CREATED)
async def start_investigation(incident_id: str, db: AsyncSession = Depends(get_db)):
    try:
        run = await InvestigationService.start_investigation(db, incident_id)
        return run
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start investigation: {str(e)}")

@router.get("/investigations/{run_id}", response_model=InvestigationRunResponse)
async def get_investigation(run_id: str, db: AsyncSession = Depends(get_db)):
    run = await InvestigationService.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Investigation run not found")
    return run

@router.get("/investigations/{run_id}/steps", response_model=List[InvestigationStepResponse])
async def get_investigation_steps(run_id: str, db: AsyncSession = Depends(get_db)):
    run = await InvestigationService.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Investigation run not found")
    steps = await InvestigationService.get_steps(db, run_id)
    return steps

@router.get("/investigations/{run_id}/evidence", response_model=List[EvidenceResponse])
async def get_investigation_evidence(run_id: str, db: AsyncSession = Depends(get_db)):
    run = await InvestigationService.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Investigation run not found")
    evidence = await InvestigationService.get_evidence(db, run_id)
    return evidence
