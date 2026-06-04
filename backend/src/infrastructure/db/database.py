import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# Load environment variables
load_dotenv("backend/.env")

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("TEST_DATABASE_URL")

if not SQLALCHEMY_DATABASE_URL:
    SQLALCHEMY_DATABASE_URL = "postgresql://postgres:password@localhost:5433/stockup_test"


# --- Async Engine (Production runtime using Psycopg 3) ---

def _make_async_url(url: str) -> str:
    """
    Convert a standard postgresql:// or postgresql+asyncpg:// URL to postgresql+psycopg:// 
    This triggers SQLAlchemy 2.0 to use the fully async Psycopg 3 driver.
    """
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
        
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    
    return url


ASYNC_DATABASE_URL = _make_async_url(SQLALCHEMY_DATABASE_URL)

async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_size=5,
    max_overflow=10,       # 5 + 10 = 15 total (matches Supabase Nano limit)
    pool_recycle=300,      # Recycle connections every 5 min
    pool_pre_ping=True,
    
    # CRITICAL FOR TRANSACTION POOLERS (Supavisor / PgBouncer):
    # prepare_threshold=None completely disables server-side prepared statements in Psycopg 3.
    # This prevents the DuplicatePreparedStatementError safely and natively.
    connect_args={
        "prepare_threshold": None
    }
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# --- Sync Engine (Alembic migrations & integration tests) ---

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# --- Dependency Injection ---

async def get_db():
    """
    FastAPI dependency that yields an async database session.
    Ensures proper cleanup and rollback under high load.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise