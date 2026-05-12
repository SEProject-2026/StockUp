import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool

# Ensure the prefix is asyncpg
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Default fallback for local testing
if not DATABASE_URL:
    DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5433/stockup_test"

# The async engine implementation
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