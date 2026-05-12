import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

load_dotenv()
load_dotenv("backend/.env")

# 1. Database URL configuration
# Ensure the URL starts with postgresql+asyncpg:// for async support
# and points to port 6543 for Supabase Transaction Pooler.
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("TEST_DATABASE_URL")

if not DATABASE_URL:
    DATABASE_URL = "postgresql+asyncpg://postgres:pass@localhost:5433/stockup_test"

# 2. Optimized Engine for Supabase Transaction Mode
# Cites: ARD 4.1.1 (Performance) and Supabase Infrastructure constraints.
engine = create_async_engine(
    DATABASE_URL,
    # NullPool is ideal when using an external pooler like Supavisor.
    # It prevents Render from holding idle connections.
    poolclass=NullPool,
    connect_args={
        # Mandatory for Transaction mode to prevent errors with prepared statements.
        "prepared_statement_cache_size": 0,
        "statement_cache_size": 0,
        # Fail fast if the pooler is saturated (Queue exceeds limits).
        "command_timeout": 10 
    }
)

# 3. Async Session Factory
AsyncSessionLocal = sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

Base = declarative_base()

# 4. Dependency Injection (Asynchronous)
async def get_db():
    """
    Yields a database session and ensures it's closed immediately
    after use to free up the Transaction Pooler slot.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()