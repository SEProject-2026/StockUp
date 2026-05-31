import os
import csv
import pytest
from unittest.mock import patch
from src.repositories.catalog_provider import CatalogItem

# Adjust the import path based on where your CsvCatalogProvider is located
from src.infrastructure.repositories.csv_catalog_provider import CsvCatalogProvider

# --- Fixtures ---

@pytest.fixture
def sample_csv_path(tmp_path):
    """Creates a temporary CSV file with varied test data."""
    file_path = tmp_path / "test_catalog.csv"
    data = [
        {"Barcode": "123", "ItemName": "Global Apple", "ManufacturerName": "Farm", "Chain": "GLOBAL", "SuggestedStorageCategory": "FRIDGE", "AverageWeight": "100", "SampleSize": "2"},
        {"Barcode": "123", "ItemName": "Local Apple", "ManufacturerName": "Local Farm", "Chain": "CHAIN_A", "SuggestedStorageCategory": "FRIDGE", "AverageWeight": "110", "SampleSize": "1"},
        {"Barcode": "7290000000456", "ItemName": "Banana", "ManufacturerName": "Import", "Chain": "GLOBAL", "SuggestedStorageCategory": "OTHER", "AverageWeight": "150", "SampleSize": "5"},
        # Invalid row to test skip logic
        {"Barcode": "", "ItemName": "", "ManufacturerName": "", "Chain": "GLOBAL", "SuggestedStorageCategory": "", "AverageWeight": "", "SampleSize": ""}
    ]
    
    with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        
    return str(file_path)

@pytest.fixture
def provider(sample_csv_path):
    """Returns an instance of CsvCatalogProvider loaded with sample data."""
    return CsvCatalogProvider(sample_csv_path)

# --- Tests ---

def test_load_data_missing_file(tmp_path):
    """Tests initialization with a non-existent file."""
    fake_path = str(tmp_path / "does_not_exist.csv")
    prov = CsvCatalogProvider(fake_path)
    assert len(prov._all_items) == 0

def test_load_data_exception(sample_csv_path):
    """Tests the empty exception block in _load_data."""
    with patch('csv.DictReader', side_effect=Exception("Simulated Read Error")):
        prov = CsvCatalogProvider(sample_csv_path)
        # Should fail silently as per your code's except Exception as e:{}
        assert len(prov._all_items) == 0

def test_get_padded_barcode(provider):
    """Tests the 13-digit padding logic."""
    assert provider._get_padded_barcode("123") == "7290000000123"
    assert provider._get_padded_barcode("7290000000456") == "7290000000456"
    assert provider._get_padded_barcode("abc") == "abc" # Non-digit fallback

@pytest.mark.asyncio
async def test_get_item_by_barcode_async(provider):
    """Tests async fetching with chain prioritization and global fallback."""
    # 1. Fetch Chain-specific item
    item_chain = await provider.get_item_by_barcode("123", "CHAIN_A")
    assert item_chain is not None
    assert item_chain.name == "Local Apple"

    # 2. Fetch Global item (fallback because CHAIN_B doesn't have it)
    item_global = await provider.get_item_by_barcode("123", "CHAIN_B")
    assert item_global is not None
    assert item_global.name == "Global Apple"

    # 3. Fetch missing item
    item_missing = await provider.get_item_by_barcode("999")
    assert item_missing is None

@pytest.mark.asyncio
async def test_get_items_by_barcodes_async(provider):
    """Tests batch fetching of barcodes."""
    items = await provider.get_items_by_barcodes(["123", "7290000000456", "999"], "CHAIN_A")
    assert len(items) == 2
    assert items[0].name == "Local Apple" # Prioritized CHAIN_A
    assert items[1].name == "Banana"      # Fallback to GLOBAL

@pytest.mark.asyncio
async def test_search_items_by_name(provider):
    """Tests search functionality, deduplication, and short queries."""
    # Too short query
    assert await provider.search_items_by_name("A") == []
    
    # Normal query (case insensitive)
    results = await provider.search_items_by_name("apple")
    assert len(results) == 2
    # Check deduplication (names must be unique in results)
    names = [r.name for r in results]
    assert "Global Apple" in names
    assert "Local Apple" in names

@pytest.mark.asyncio
async def test_search_items_by_name_limit(provider):
    """Tests the 20-item hard limit on search."""
    # Inject 25 items with similar names
    for i in range(25):
        provider._all_items.append(CatalogItem(
            barcode=str(i), name=f"TestItem {i}", manufacturer="", 
            chain_source="GLOBAL", location="OTHER", weight=0, sample_size=0
        ))
    
    results = await provider.search_items_by_name("testitem")
    assert len(results) == 20 # Should break at 20

@pytest.mark.asyncio
async def test_update_weighted_mem_only(provider):
    """Tests the moving average mathematical logic."""
    barcode = "123"
    
    # Global Apple initial: Weight=100, Size=2 -> Total = 200
    await provider.update_weighted_mem_only(barcode, "GLOBAL", 160.0)
    
    item = provider._get_item_sync(barcode, "GLOBAL")
    # New Size should be 3. New Total = 360. New Average = 120.
    assert item.sample_size == 3
    assert item.weight == 120.0

@pytest.mark.asyncio
async def test_update_weighted_mem_only_missing(provider):
    """Tests updating a non-existent item (should silently return)."""
    await provider.update_weighted_mem_only("999", "GLOBAL", 100.0) # Shouldn't crash

@pytest.mark.asyncio
async def test_persist(provider, tmp_path):
    """Tests the atomic write to CSV."""
    await provider.update_weighted_mem_only("123", "GLOBAL", 160.0) # Change data
    
    await provider.persist()
    
    # Reload from the written file to verify
    new_provider = CsvCatalogProvider(provider.csv_path)
    updated_item = new_provider._get_item_sync("123", "GLOBAL")
    
    assert updated_item.sample_size == 3
    assert updated_item.weight == 120.0

@pytest.mark.asyncio
async def test_persist_exception(provider):
    """Tests temp file cleanup if an exception occurs during persistence."""
    # Force shutil.move to throw an error to trigger the except block
    with patch('shutil.move', side_effect=Exception("Simulated move error")):
        # We need to spy on os.remove to ensure the temp file is cleaned up
        with patch('os.remove') as mock_remove:
            await provider.persist()
            mock_remove.assert_called_once()