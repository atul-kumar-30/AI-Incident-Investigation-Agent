from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.core.config import settings
from app.core.logging import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up AI Incident Investigation Agent API")
    yield
    logger.info("Shutting down AI Incident Investigation Agent API")

app = FastAPI(
    title="AI Incident Investigation Agent",
    version="1.0.0",
    description="Phase 1 - Application Foundation",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
