import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.main import app
from app.db.session import get_db, Base
from app.db import session as db_session_module

# If USE_POSTGRES is set, we will use testcontainers, otherwise SQLite
USE_POSTGRES = os.getenv("USE_POSTGRES", "0") == "1"

postgres_container = None

if USE_POSTGRES:
    from testcontainers.postgres import PostgresContainer
    postgres_container = PostgresContainer("pgvector/pgvector:pg15")
    postgres_container.start()
    
    # testcontainers provides sync URL, we need asyncpg
    sync_url = postgres_container.get_connection_url()
    TEST_DATABASE_URL = sync_url.replace("postgresql+psycopg2", "postgresql+asyncpg")
    
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
else:
    from sqlalchemy.pool import StaticPool
    TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(
        TEST_DATABASE_URL, 
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Override the AsyncSessionLocal globally for tests
db_session_module.AsyncSessionLocal = TestingSessionLocal

@pytest_asyncio.fixture(scope="session")
async def db_engine():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    
    if postgres_container:
        postgres_container.stop()

@pytest_asyncio.fixture
async def db_session(db_engine):
    async with TestingSessionLocal() as session:
        yield session

@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
