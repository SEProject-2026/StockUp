import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

load_dotenv()

# Ensure the prefix is asyncpg for async driver support
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("TEST_DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Default fallback for local testing
if not DATABASE_URL:
    DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5433/stockup_test"

# --- CRITICAL: Define Base here so models can import it ---
Base = declarative_base()

# The async engine implementation optimized for Supabase Transaction Mode
engine = create_async_engine(
    DATABASE_URL,
    poolclass=NullPool,  # Mandatory for Supabase Supavisor
    connect_args={
        "prepared_statement_cache_size": 0,  # Required for Transaction mode
        "statement_cache_size": 0
    }
)

AsyncSessionLocal = sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Dependency for FastAPI routes
async def get_db():
    """
    Yields an async session and ensures it is closed after the request.
    Cites: ARD 4.1.2 (Reliability and Stability)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()