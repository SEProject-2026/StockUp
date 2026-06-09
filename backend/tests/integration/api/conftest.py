import os
import pytest
import uuid
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from httpx import AsyncClient, ASGITransport

from tests.factories import create_home_entity, create_user_entity
from src.main import app
from src.api.security import get_current_user_id
from src.infrastructure.db.database import Base, get_db, _make_async_url

@pytest.fixture(scope="session")
def event_loop_policy():
    """psycopg3 requires a selector-based event loop for async operations."""
    policy = getattr(asyncio, "WindowsSelectorEventLoopPolicy", asyncio.DefaultEventLoopPolicy)
    return policy()

@pytest.fixture(autouse=True)
def mock_scheduler(mocker):
    """
    Disables the background scheduler during tests to avoid loop mismatch issues
    and database access outside the test transaction.
    """
    mocker.patch("src.timed_alert_jobs.scheduler.start")
    mocker.patch("src.timed_alert_jobs.scheduler.shutdown")

# ==========================================
# 1. Infrastructure Setup (PostgreSQL)
# ==========================================

TEST_DATABASE_URL = "postgresql://user:password@localhost:5433/stockup_test"

# Sync engine — used only for schema setup and cleanup (DDL operations)
sync_engine = create_engine(TEST_DATABASE_URL, poolclass=NullPool)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """
    Initializes the database schema once per session using the sync engine.
    """
    print("\n[DEBUG] setup_test_db started", flush=True)
    Base.metadata.create_all(bind=sync_engine)
    print("[DEBUG] setup_test_db finished", flush=True)
    yield
    # Base.metadata.drop_all(bind=sync_engine)

@pytest.fixture(scope="session")
def async_db_resources():
    """
    Creates the async engine and sessionmaker once per session.
    Using NullPool to avoid event loop mismatch issues across tests.
    """
    print("\n[DEBUG] async_db_resources started", flush=True)
    engine = create_async_engine(
        _make_async_url(TEST_DATABASE_URL),
        poolclass=NullPool,
        connect_args={"prepare_threshold": None}
    )
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    print("[DEBUG] async_db_resources finished", flush=True)
    return engine, session_factory

# ==========================================
# 2. Database Lifecycle Fixtures
# ==========================================

@pytest.fixture
async def db_session(async_db_resources):
    """
    Provides an isolated async database session for each test.
    """
    print("\n[DEBUG] db_session fixture started", flush=True)
    engine, session_factory = async_db_resources
    async with session_factory() as session:
        print("[DEBUG] db_session yielded", flush=True)
        yield session
        print("[DEBUG] db_session closing")
        
    # Active cleanup: Delete all rows instead of truncate to avoid heavy locks
    async with engine.connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(text(f'DELETE FROM "{table.name}";'))
        await conn.commit()

# ==========================================
# 3. FastAPI & Security Fixtures
# ==========================================

@pytest.fixture
async def client(async_db_resources):
    """
    Provides an httpx AsyncClient with the database dependency overridden.
    Yields a fresh session for each request to avoid loop sharing issues.
    """
    print("\n[DEBUG] client fixture started")
    engine, session_factory = async_db_resources
    
    async def override_get_db():
        async with session_factory() as session:
            yield session
            
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        print("[DEBUG] client yielded")
        yield c
        print("[DEBUG] client closing")

@pytest.fixture
def auth_user():
    """
    Returns a random user ID and overrides security dependency to return it.
    """
    user_id = uuid.uuid4()
    app.dependency_overrides[get_current_user_id] = lambda: user_id
    return user_id

@pytest.fixture
async def active_home(db_session, auth_user):
    """
    Creates a user and a home in the DB and returns the home entity.
    We COMMIT here so the app's session can see it.
    """
    user = create_user_entity(db=db_session, user_id=auth_user)
    home = create_home_entity(db=db_session, admin_user=user)
    
    await db_session.commit() # Commit to make visible to other sessions
    return home

@pytest.fixture
async def home_headers(active_home):
    """
    Injects the active home ID into request headers.
    """
    return {"X-Home-ID": str(active_home.id)}

@pytest.fixture(autouse=True)
def clean_dependency_overrides():
    """Clears FastAPI dependency overrides after each test to prevent leaks."""
    yield
    app.dependency_overrides.clear()