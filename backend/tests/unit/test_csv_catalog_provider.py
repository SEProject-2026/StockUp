import os
import csv
import pytest
import tempfile
from src.infrastructure.repositories.csv_catalog_provider import CsvCatalogProvider

# === Setup: Create a temporary CSV with English Chain names ===
@pytest.fixture
def temp_csv_path():
    """
    Creates a temporary CSV file with Hebrew product names but English chain keys.
    """
    fd, path = tempfile.mkstemp(suffix=".csv")
    
    # Define dummy data using English Chain names
    data = [
        # Case 1: Same barcode, specific chain override
        {"Barcode": "100", "ItemName": "חלב תנובה", "Chain": "GLOBAL", "ManufacturerName": "Tnuva"},
        {"Barcode": "100", "ItemName": "חלב תנובה במבצע", "Chain": "rami_levi", "ManufacturerName": "Tnuva"}, 
        
        # Case 2: Item exists only globally
        {"Barcode": "200", "ItemName": "לחם אחיד", "Chain": "GLOBAL", "ManufacturerName": "Angel"},
        
        # Case 3: Deduplication Logic
        {"Barcode": "300", "ItemName": "מלפפון", "Chain": "GLOBAL", "ManufacturerName": ""}, # Shortest name
        {"Barcode": "301", "ItemName": "מלפפון טרי", "Chain": "shufersal", "ManufacturerName": ""}, # Longer name
        {"Barcode": "302", "ItemName": "מלפפון", "Chain": "victory", "ManufacturerName": ""}, # Duplicate name
    ]
    
    # Write to CSV with utf-8-sig to handle Hebrew product names correctly
    with os.fdopen(fd, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=["Barcode", "ItemName", "Chain", "ManufacturerName"])
        writer.writeheader()
        writer.writerows(data)
        
    yield path
    os.remove(path)

# === The Tests ===

@pytest.mark.asyncio
async def test_get_item_global_fallback(temp_csv_path):
    """
    Test fallback logic.
    Asking for 'Bread' in 'rami_levi' (which doesn't exist for this barcode) 
    should return the Global version.
    """
    provider = CsvCatalogProvider(temp_csv_path)
    
    item = await provider.get_item_by_barcode("200", chain_name="rami_levi")
    
    assert item is not None
    assert item.name == "לחם אחיד"
    assert item.chain_source == "GLOBAL"

@pytest.mark.asyncio
async def test_get_item_chain_specific(temp_csv_path):
    """
    Test retrieving a chain-specific item.
    Requesting 'rami_levi' should find the specific row.
    """
    provider = CsvCatalogProvider(temp_csv_path)
    
    # Request specific item from Rami Levi
    item = await provider.get_item_by_barcode("100", chain_name="rami_levi")
    
    assert item is not None
    assert item.name == "חלב תנובה במבצע"
    assert item.chain_source == "rami_levi" 

@pytest.mark.asyncio
async def test_search_deduplication_hebrew(temp_csv_path):
    """
    Test deduplication logic with Hebrew product names.
    We have "מלפפון" (Global) and "מלפפון" (Victory).
    We should only get one "מלפפון" in the results to prevent clutter.
    """
    provider = CsvCatalogProvider(temp_csv_path)
    
    # Search for "מלפפון"
    results = await provider.search_items_by_name("מלפפון")
    
    names = [i.name for i in results]
    
    # Assertions:
    # 1. We expect the exact match "מלפפון"
    assert "מלפפון" in names
    # 2. We expect the variation "מלפפון טרי"
    assert "מלפפון טרי" in names
    # 3. We expect "מלפפון" to appear EXACTLY ONCE
    assert names.count("מלפפון") == 1
    
    # Verify sorting: The first result should be the Global one
    # (Prioritizing Global source and shortest name)
    assert results[0].chain_source == "GLOBAL"