import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# Load environment variables from the specific backend .env file
load_dotenv("backend/.env")

# 1. Fallback mechanism: check both common names
# This ensures that if CI uses one name and local dev uses another, it still works.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("TEST_DATABASE_URL")

# 2. Safety Check: If both are None (common during CI collection phase)
# or empty, provide a valid local fallback to prevent SQLAlchemy from crashing.
if not SQLALCHEMY_DATABASE_URL:
    SQLALCHEMY_DATABASE_URL = "postgresql://postgres:password@localhost:5433/stockup_test"


# --- Async Engine (Production runtime) ---

def _make_async_url(url: str) -> str:
    """Convert a standard postgresql:// URL to postgresql+asyncpg:// for the async driver."""
    if url.startswith("postgresql+asyncpg://"):
        return url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


ASYNC_DATABASE_URL = _make_async_url(SQLALCHEMY_DATABASE_URL)

async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_size=5,
    max_overflow=10,       # 5 + 10 = 15 total (matches Supabase Nano limit)
    pool_recycle=300,      # Recycle connections every 5 min to avoid stale pooler slots
    pool_pre_ping=True,
    
    # CRITICAL FOR TRANSACTION POOLER (Supavisor):
    # Pass driver-specific arguments directly to asyncpg via connect_args.
    # This bypasses SQLAlchemy's strict validation and disables caching correctly.
    connect_args={
        "statement_cache_size": 0,          # Disables asyncpg prepared statement cache
        "max_cached_statement_lifetime": 0, # Ensures statements aren't cached by lifetime
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


# --- Dependency Injection (FastAPI lifecycle management) ---

async def get_db():
    """
    FastAPI dependency that yields an async database session.
    Ensures proper cleanup and rollback under high load or concurrency.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise