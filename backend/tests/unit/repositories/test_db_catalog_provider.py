import pytest
from unittest.mock import patch
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, declarative_base

# Adjust these imports based on your project structure
from src.repositories.catalog_provider import CatalogItem
from src.infrastructure.repositories.db_catalog_provider import DbCatalogProvider

# --- 1. Mock DB Model & Setup ---
# We define a dummy model here so the tests can run entirely in isolation
# without needing your actual Postgres/DB setup.
Base = declarative_base()

class MockCatalogItemModel(Base):
    __tablename__ = 'catalog_items'
    id = Column(Integer, primary_key=True, autoincrement=True)
    barcode = Column(String, index=True)
    name = Column(String)
    manufacturer = Column(String)
    chain = Column(String)
    location = Column(String)
    avg_weight = Column(Float)
    sample_size = Column(Integer)

@pytest.fixture(scope="function")
def db_session():
    """Creates a fresh in-memory SQLite database for every test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()

@pytest.fixture(scope="function")
def seeded_db(db_session):
    """Seeds the in-memory database with test data."""
    # Note: Using valid Enums for location based on our previous findings!
    items = [
        MockCatalogItemModel(barcode="123", name="Global Apple", manufacturer="Farm", chain="GLOBAL", location="FRIDGE", avg_weight=100.0, sample_size=2),
        MockCatalogItemModel(barcode="123", name="Local Apple", manufacturer="Local Farm", chain="CHAIN_A", location="FRIDGE", avg_weight=110.0, sample_size=1),
        MockCatalogItemModel(barcode="7290000000456", name="Banana", manufacturer="Import", chain="GLOBAL", location="OTHER", avg_weight=150.0, sample_size=5),
    ]
    db_session.add_all(items)
    db_session.commit()
    return db_session

@pytest.fixture
def provider(seeded_db):
    """Returns the provider connected to the seeded in-memory DB."""
    # We patch the provider's reference to CatalogItemModel to use our Mock model
    with patch('src.infrastructure.repositories.db_catalog_provider.CatalogItemModel', MockCatalogItemModel):
        yield DbCatalogProvider(db=seeded_db)

# --- 2. Tests ---

def test_map_to_domain(provider):
    """Tests proper mapping from SQLAlchemy model to Pydantic Domain model."""
    db_model = MockCatalogItemModel(
        barcode="999", name="Test", manufacturer="TestMfg", 
        chain="GLOBAL", location="OTHER", avg_weight=50.0, sample_size=1
    )
    domain_model = provider._map_to_domain(db_model)
    
    assert domain_model.barcode == "999"
    assert domain_model.name == "Test"
    assert domain_model.weight == 50.0 # Checking the avg_weight -> weight map

def test_get_padded_barcode(provider):
    """Tests the Israeli barcode padding helper."""
    assert provider._get_padded_barcode("123") == "7290000000123"
    assert provider._get_padded_barcode("7290000000456") == "7290000000456"

@pytest.mark.asyncio
async def test_get_item_by_barcode(provider):
    """Tests fetching single items with chain priorities and padding fallbacks."""
    # 1. Exact chain match
    chain_item = await provider.get_item_by_barcode("123", "CHAIN_A")
    assert chain_item.name == "Local Apple"
    assert chain_item.barcode == "123" # Should restore original unpadded barcode

    # 2. Fallback to GLOBAL if chain doesn't exist
    global_item = await provider.get_item_by_barcode("123", "CHAIN_B")
    assert global_item.name == "Global Apple"

    # 3. Padded lookup (DB has 729...456, we search '456')
    padded_item = await provider.get_item_by_barcode("456", "GLOBAL")
    assert padded_item.name == "Banana"
    assert padded_item.barcode == "456" # Should restore the '456' we requested

    # 4. Missing item
    missing = await provider.get_item_by_barcode("999")
    assert missing is None

@pytest.mark.asyncio
async def test_get_items_by_barcodes(provider):
    """Tests bulk fetching, deduplication, and sorting."""
    # Empty list edge case
    assert await provider.get_items_by_barcodes([]) == []

    # Fetch mixture of items
    results = await provider.get_items_by_barcodes(["123", "456", "999"], "CHAIN_A")
    
    assert len(results) == 2
    names = [r.name for r in results]
    assert "Local Apple" in names # Prioritized CHAIN_A
    assert "Banana" in names      # Handled the '456' padding to find it

@pytest.mark.asyncio
async def test_search_items_by_name(provider):
    """Tests the ILIKE database text search."""
    # Too short
    assert await provider.search_items_by_name("A") == []

    # Case insensitive search
    results = await provider.search_items_by_name("apple")
    assert len(results) == 2
    # Ensure priority sort (CHAIN before GLOBAL)
    assert results[0].chain_source == "GLOBAL"
    assert results[1].chain_source == "CHAIN_A"

def test_update_weighted_mem_only(provider, seeded_db):
    """Tests the moving average math and DB flush logic."""
    barcode = "123"
    
    # Update the GLOBAL apple (Initial: weight=100, size=2, total=200)
    provider.update_weighted_mem_only(barcode, "GLOBAL", 160.0)
    
    # Because flush() writes to the session buffer, we can query it directly
    updated_model = seeded_db.query(MockCatalogItemModel).filter_by(name="Global Apple").first()
    
    # New size = 3, New Total = 360, New Avg = 120
    assert updated_model.sample_size == 3
    assert updated_model.avg_weight == 120.0

def test_update_weighted_mem_only_missing(provider):
    """Ensures updating a missing item doesn't crash."""
    # Should safely return without executing math
    provider.update_weighted_mem_only("999", "GLOBAL", 50.0)

def test_persist_success(provider, seeded_db):
    """Tests successful commit."""
    # Change some data
    provider.update_weighted_mem_only("123", "GLOBAL", 160.0)
    
    # Patch commit to verify it's called
    with patch.object(seeded_db, 'commit') as mock_commit:
        provider.persist()
        mock_commit.assert_called_once()

def test_persist_exception(provider, seeded_db):
    """Tests rollback triggers on exception."""
    # Force the commit to throw an error
    with patch.object(seeded_db, 'commit', side_effect=Exception("DB Failure")):
        with patch.object(seeded_db, 'rollback') as mock_rollback:
            with pytest.raises(Exception, match="DB Failure"):
                provider.persist()
            
            mock_rollback.assert_called_once()