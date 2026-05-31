import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# Load environment variables from the specific backend .env file
load_dotenv("backend/.env")

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("TEST_DATABASE_URL")

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
    # Disable prepared statement caching at the asyncpg driver level.
    # Required for pgbouncer in transaction/statement pool mode.
    connect_args={
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
    },
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