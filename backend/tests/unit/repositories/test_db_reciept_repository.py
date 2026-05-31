import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4, UUID
from unittest.mock import patch
from sqlalchemy import create_engine, Column, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
import pytest_asyncio

from src.domain.receipt.receipt import ReceiptDTO, ReceiptItemDTO
from src.domain.enums import UnitType, LocationType
# Adjust this import to match your actual file path
from src.infrastructure.repositories.db_receipt_repository import DbReceiptRepository

# --- 1. Mock DB Models & Setup ---
Base = declarative_base()

class MockReceiptRecordModel(Base):
    __tablename__ = 'receipts'
    id = Column(String, primary_key=True)
    home_id = Column(String, index=True)
    user_id = Column(String)
    chain = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    items = relationship("MockReceiptRecordItemModel", back_populates="receipt", cascade="all, delete-orphan")

class MockReceiptRecordItemModel(Base):
    __tablename__ = 'receipt_items'
    id = Column(String, primary_key=True)
    receipt_id = Column(String, ForeignKey('receipts.id'))
    name = Column(String)
    barcode = Column(String)
    quantity = Column(Float)
    
    receipt = relationship("MockReceiptRecordModel", back_populates="items")

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

@pytest_asyncio.fixture(scope="function")
async def db_session():
    # Initialize the async engine
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    
    async with SessionLocal() as session:
        yield session
        
    # Dispose the engine to close all background connections and free the event loop
    await engine.dispose()

@pytest_asyncio.fixture
async def repo(db_session):
    """Returns the repository connected to the mocked in-memory models."""
    # We patch the models inside your repository file so it uses our mock SQLite ones
    # Adjust 'db_receipt_repository' below to match your actual file name
    with patch('src.infrastructure.repositories.db_receipt_repository.ReceiptRecordModel', MockReceiptRecordModel):
        with patch('src.infrastructure.repositories.db_receipt_repository.ReceiptRecordItemModel', MockReceiptRecordItemModel):
            yield DbReceiptRepository(db=db_session)

# --- 2. Tests ---

@pytest.mark.asyncio
async def test_save_receipt(repo, db_session):
    """Tests that a receipt and its items are correctly saved to the DB."""
    receipt_id = uuid4()
    home_id = uuid4()
    user_id = uuid4()
    
    dto = ReceiptDTO(
        id=receipt_id,
        home_id=home_id,
        user_id=user_id,
        chain="GLOBAL",
        items=[
            ReceiptItemDTO(name="Apple", barcode="123", quantity=2, unit=UnitType.UNIT, location=LocationType.OTHER, weight=1.0),
            ReceiptItemDTO(name="Banana", barcode="456", quantity=1.5, unit=UnitType.UNIT, location=LocationType.OTHER, weight=1.5)
        ]
    )
    
    await repo.save(dto)
    
    # Verify via direct DB query
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    result = await db_session.execute(
        select(MockReceiptRecordModel)
        .options(selectinload(MockReceiptRecordModel.items))
        .filter_by(id=str(receipt_id))
    )
    saved_receipt = result.scalars().first()
    assert saved_receipt is not None
    assert saved_receipt.home_id == str(home_id)
    assert len(saved_receipt.items) == 2
    
    item_names = [item.name for item in saved_receipt.items]
    assert "Apple" in item_names
    assert "Banana" in item_names

@pytest.mark.asyncio
async def test_get_by_home_logic_and_mapping(repo, db_session):
    """Tests fetching by home_id and validates the integer/float quantity logic."""
    target_home = uuid4()
    other_home = uuid4()
    
    # 1. Add record for Target Home
    rec1 = MockReceiptRecordModel(id=str(uuid4()), home_id=str(target_home), user_id=str(uuid4()), chain="CHAIN_A")
    # Whole number quantity (should remain as quantity)
    item_whole = MockReceiptRecordItemModel(id=str(uuid4()), name="Apple", barcode="111", quantity=3.0)
    # Fractional quantity (should default to 1, and weight should hold the float)
    item_float = MockReceiptRecordItemModel(id=str(uuid4()), name="Chicken", barcode="222", quantity=1.25)
    rec1.items.extend([item_whole, item_float])
    
    # 2. Add record for Other Home (Should be ignored by query)
    rec2 = MockReceiptRecordModel(id=str(uuid4()), home_id=str(other_home), user_id=str(uuid4()), chain="CHAIN_B")
    
    db_session.add_all([rec1, rec2])
    await db_session.commit()
    
    # Fetch
    results = await repo.get_by_home(target_home)
    
    # Assertions
    assert len(results) == 1
    assert results[0].chain == "CHAIN_A"
    assert len(results[0].items) == 2
    
    # Check the mapping logic
    for item in results[0].items:
        if item.name == "Apple":
            assert item.quantity == 3   # 3.0 becomes 3
            assert item.weight == 3.0
        elif item.name == "Chicken":
            assert item.quantity == 1   # 1.25 isn't an integer, falls back to 1
            assert item.weight == 1.25

@pytest.mark.asyncio
async def test_get_by_home_with_since(repo, db_session):
    """Tests the datetime filtering logic."""
    home_id = uuid4()
    now = datetime.now(timezone.utc)
    
    # Old receipt (Outside 'since' window)
    old_rec = MockReceiptRecordModel(id=str(uuid4()), home_id=str(home_id), user_id=str(uuid4()), chain="OLD", created_at=now - timedelta(days=10))
    
    # New receipt (Inside 'since' window)
    new_rec = MockReceiptRecordModel(id=str(uuid4()), home_id=str(home_id), user_id=str(uuid4()), chain="NEW", created_at=now)
    
    db_session.add_all([old_rec, new_rec])
    await db_session.commit()
    
    # Query for last 5 days
    since_date = now - timedelta(days=5)
    results = await repo.get_by_home(home_id, since=since_date)
    
    assert len(results) == 1
    assert results[0].chain == "NEW"

@pytest.mark.asyncio
async def test_get_by_home_limit_and_ordering(repo, db_session):
    """Tests that results are limited and ordered by created_at DESC."""
    home_id = uuid4()
    now = datetime.now(timezone.utc)
    
    # Add 3 receipts spaced out by 1 day
    for i in range(3):
        rec = MockReceiptRecordModel(
            id=str(uuid4()), home_id=str(home_id), user_id=str(uuid4()), 
            chain=f"CHAIN_{i}", created_at=now - timedelta(days=i)
        )
        db_session.add(rec)
    await db_session.commit()
    
    # Limit to 2
    results = await repo.get_by_home(home_id, limit=2)
    
    assert len(results) == 2
    # Should get the newest ones first (days=0, then days=1)
    assert results[0].chain == "CHAIN_0" 
    assert results[1].chain == "CHAIN_1"