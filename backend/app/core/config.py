from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    APP_ENV: str = "development"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/incident_investigator"
    CORS_ORIGINS: List[str] = ["http://localhost:5180", "http://localhost:3000", "http://localhost:5181", "http://127.0.0.1:5181"]
    
    # LLM Configuration
    LLM_PROVIDER: str = "google"
    LLM_MODEL: str = "gemini-2.0-flash"
    LLM_API_KEY: str = "MOCK_KEY"
    LLM_TEMPERATURE: float = 0.0
    
    # Embedding Configuration
    EMBEDDING_PROVIDER: str = "google"
    EMBEDDING_MODEL: str = "gemini-embedding-2"
    EMBEDDING_DIMENSION: int = 768
    
    # Phase 4
    REPOSITORY_ALLOWED_ROOT: str = os.getenv(
        "REPOSITORY_ALLOWED_ROOT", 
        "/app/demo_repositories" if os.path.exists("/app/demo_repositories") 
        else os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "demo_repositories"))
    )

    class Config:
        extra = "ignore"
        env_file = ".env"
        # In case we run from backend folder or root folder
        if os.path.exists("../.env"):
            env_file = "../.env"
        elif os.path.exists(".env"):
            env_file = ".env"

settings = Settings()
