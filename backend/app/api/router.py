from fastapi import APIRouter
from app.api.routes import health, incidents, investigations, logs, repositories, documents, hypotheses, verifications

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
api_router.include_router(documents.router, tags=["documents"])
api_router.include_router(investigations.router, tags=["investigations"])
api_router.include_router(logs.router, tags=["logs"])
api_router.include_router(repositories.router, tags=["repositories"])
api_router.include_router(hypotheses.router, tags=["hypotheses"])
api_router.include_router(verifications.router, tags=["verifications"])
