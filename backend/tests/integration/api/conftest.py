import os
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.infrastructure.db.database import Base, get_db
from src.api.security import get_current_user_id

# 1. Infrastructure Setup: Load Test DB URL
# Ensure TEST_DATABASE_URL is set in your .env.test or docker-compose
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

if not TEST_DATABASE_URL:
    raise ValueError("TEST_DATABASE_URL environment variable is not set")

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Database Fixtures ---

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """
    Creates all database tables once at the start of the test session.
    """
    Base.metadata.create_all(bind=engine)
    yield
    # Tables are preserved for debugging. Use 'drop_all' if a fresh schema is needed per run.
    # Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    """
    Provides an isolated database session for each test using a transaction rollback.
    This ensures that data created in one test does not leak into another.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

# --- API & Security Fixtures ---

@pytest.fixture
def client(db_session):
    """
    Standard FastAPI TestClient with the database dependency overridden
     to use the isolated test session.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    # Clear overrides after the test to avoid side effects
    app.dependency_overrides.clear()

@pytest.fixture
def auth_user(client):
    """
    Bypasses Supabase JWT verification and injects a fixed User ID.
    Usage: Inject 'auth_user' into any test requiring an authenticated user.
    """
    fixed_user_id = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
    
    async def mocked_user_id():
        return fixed_user_id
        
    app.dependency_overrides[get_current_user_id] = mocked_user_id
    yield fixed_user_id
    # Ensure security overrides are cleared after the test
    app.dependency_overrides.clear()