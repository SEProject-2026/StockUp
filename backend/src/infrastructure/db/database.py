import os
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker, declarative_base


load_dotenv()  
load_dotenv("backend/.env")

# 1. Fallback mechanism: check both common names
# This ensures that if CI uses one name and local dev uses another, it still works.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("TEST_DATABASE_URL")

# 2. Safety Check: If both are None (common during CI collection phase),
# we provide a dummy string to prevent SQLAlchemy from raising an ArgumentError.
if SQLALCHEMY_DATABASE_URL is None:
    # This URL won't actually be used by tests because the Container overrides it,
    # but it allows the 'engine' object to be created without crashing the import.
    SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost:5432/placeholder_db"

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


# (Dependency Injection — now async)
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise