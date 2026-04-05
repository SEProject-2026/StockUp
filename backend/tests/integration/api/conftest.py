import os
import pytest
import uuid
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from tests.factories import create_home_entity, create_user_entity
from src.main import app
from src.infrastructure.db.database import Base, get_db
from src.api.security import get_current_user_id

# ==========================================
# 1. Infrastructure Setup (PostgreSQL)
# ==========================================

TEST_DATABASE_URL = "postgresql://user:password@localhost:5433/stockup_test"

engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ==========================================
# 2. Database Lifecycle Fixtures
# ==========================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """
    Initializes the database schema once per session.
    """
    from src.infrastructure.db import models 
    
    Base.metadata.create_all(bind=engine)
    yield
    # Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    """
    Provides an isolated database session for each test.
    Forces a truncate on all tables after execution to ensure 
    a clean state even if internal commits were triggered.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    
    # Active cleanup: Truncate all tables to prevent data leakage
    with engine.connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(text(f'TRUNCATE TABLE "{table.name}" CASCADE;'))
        conn.commit()
        
    connection.close()

# ==========================================
# 3. FastAPI & Security Fixtures
# ==========================================

@pytest.fixture
def client(db_session):
    """
    Provides a FastAPI TestClient with the database dependency overridden.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as c:
        yield c
    
    app.dependency_overrides.clear()

@pytest.fixture
def auth_user(client):
    """
    Injects a fixed User ID into the security dependency.
    """
    fixed_user_id = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
    app.dependency_overrides[get_current_user_id] = lambda: fixed_user_id
    return fixed_user_id

@pytest.fixture
def active_home(db_session, auth_user):
    """
    Creates a user and a home in the DB and returns the home entity.
    Uses flush() instead of commit() to allow the rollback mechanism 
    to handle cleanup properly.
    """
    create_user_entity(db=db_session, user_id=auth_user)
    home = create_home_entity(db=db_session, admin_user_id=auth_user)
    
    db_session.flush()
    return home

@pytest.fixture
def home_headers(active_home):
    """
    Returns the standard headers required for home-specific routes.
    """
    return {"X-Home-ID": str(active_home.id)}