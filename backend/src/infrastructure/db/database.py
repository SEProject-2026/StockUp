import os
from sqlalchemy import create_engine
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

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# (Dependency Injection)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()