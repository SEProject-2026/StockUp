import pytest
from datetime import date
from unittest.mock import AsyncMock, patch
from src.repositories.catalog_provider import CatalogItem

# ==========================================
# 1. Product & Item Management
# ==========================================

async def test_add_product_success(client, home_headers):
    """Scenario: User adds a product to their active home."""
    payload = {
        "name": "Milk",
        "quantity": 2,
        "barcode": "123456",
        "expiration_date": str(date.today()),
        "location": "FRIDGE",
        "nickname": "Soy Milk"
    }
    
    response = await client.post("/stock/add", json=payload, headers=home_headers)
    
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["original_name"] == "Milk"
    assert data["items"][0]["quantity"] == 2
    assert "id" in data["items"][0]

async def test_update_item_quantity_success(client, home_headers):
    """Scenario: Update quantity of a specific item via patch."""
    # 1. Add Product
    add_res = await client.post("/stock/add", json={"name": "Eggs", "quantity": 12}, headers=home_headers)
    product_id = add_res.json()["data"]["id"]
    item_id = add_res.json()["data"]["items"][0]["id"]
    
    # 2. Update
    response = await client.patch(
        f"/stock/{product_id}/items/{item_id}/quantity", 
        json={"new_quantity": 6}, 
        headers=home_headers
    )
    
    assert response.status_code == 200
    assert response.json()["data"]["total_quantity"] == 6

async def test_update_item_expiration_success(client, home_headers):
    """Scenario: Update the expiration date of an item."""
    add_res = await client.post("/stock/add", json={"name": "Yogurt", "quantity": 1}, headers=home_headers)
    product_id = add_res.json()["data"]["id"]
    item_id = add_res.json()["data"]["items"][0]["id"]
    
    new_date = "2026-12-31"
    response = await client.patch(
        f"/stock/{product_id}/items/{item_id}/expiration", 
        json={"new_date": new_date}, 
        headers=home_headers
    )
    
    assert response.status_code == 200
    assert response.json()["data"]["items"][0]["expiration_date"] == new_date

async def test_remove_item_fully_deletes_product(client, home_headers):
    """Scenario: Removing the last remaining item deletes the product parent."""
    add_res = await client.post("/stock/add", json={"name": "Apple", "quantity": 1}, headers=home_headers)
    p_id = add_res.json()["data"]["id"]
    i_id = add_res.json()["data"]["items"][0]["id"]
    
    response = await client.delete(f"/stock/{p_id}/items/{i_id}", headers=home_headers)
    
    assert response.status_code == 200
    assert response.json()["data"] is None

# ==========================================
# 2. Filtering & Search
# ==========================================

async def test_filter_by_location(client, home_headers):
    """Scenario: Fetch products only for a specific storage category."""
    await client.post("/stock/add", json={"name": "Ice Cream", "quantity": 1, "location": "FREEZER"}, headers=home_headers)
    await client.post("/stock/add", json={"name": "Bread", "quantity": 1, "location": "PANTRY"}, headers=home_headers)
    
    response = await client.get("/stock/filter", params={"location": "FREEZER"}, headers=home_headers)
    
    assert response.status_code == 200
    assert len(response.json()["data"]) == 1
    assert response.json()["data"][0]["original_name"] == "Ice Cream"

async def test_get_all_products(client, home_headers):
    """Scenario: Retrieve list of all inventory in the home."""
    await client.post("/stock/add", json={"name": "Banana", "quantity": 5}, headers=home_headers)
    await client.post("/stock/add", json={"name": "Apple", "quantity": 3}, headers=home_headers)
    
    response = await client.get("/stock/all", headers=home_headers)
    
    assert response.status_code == 200
    assert len(response.json()["data"]) >= 2

# ==========================================
# 3. Catalog & Receipts
# ==========================================

async def test_catalog_barcode_lookup(client, home_headers):
    """Scenario: Search external catalog via mocked provider."""
    mock_item = CatalogItem(barcode="7290123", name="Scanned Bamba", manufacturer="Osem")
    
    with patch("src.infrastructure.app_container.AppContainer.get_catalog_provider") as mock_factory:
        provider = AsyncMock()
        provider.get_item_by_barcode.return_value = mock_item
        mock_factory.return_value = provider
        
        response = await client.get("/stock/catalog/barcode/7290123", headers=home_headers)
        
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "Scanned Bamba"

async def test_add_receipt_endpoint_success(client, home_headers):
    """Scenario: Process a full receipt with multiple items."""
    payload = {
        "chain": "victory",
        "items": [
            {"name": "Milk", "quantity": 2.0, "location": "FRIDGE"},
            {"name": "Pasta", "quantity": 1.0, "location": "PANTRY"}
        ]
    }
    response = await client.post("/stock/add-receipt", json=payload, headers=home_headers)
    assert response.status_code == 200
    assert response.json()["data"]["added_count"] == 2

async def test_add_receipt_duplicate_items(client, home_headers):
    """Scenario: Receipt contains the same product twice (e.g., two different sizes or batches)."""
    payload = {
        "chain": "shufersal",
        "items": [
            {"name": "Yogurt", "quantity": 1, "location": "FRIDGE"},
            {"name": "Yogurt", "quantity": 2, "location": "FRIDGE"}
        ]
    }
    response = await client.post("/stock/add-receipt", json=payload, headers=home_headers)
    
    assert response.status_code == 200
    
    # Verify DB state: Items with same location and date should MERGE
    get_res = await client.get("/stock/filter", params={"query": "Yogurt"}, headers=home_headers)
    product = get_res.json()["data"][0]
    assert product["total_quantity"] == 3
    assert len(product["items"]) == 1 # Merged because same location/date

async def test_add_receipt_updates_existing_stock(client, home_headers):
    """Scenario: Adding a receipt containing an item already in inventory."""
    # 1. Add "Eggs" manually
    await client.post("/stock/add", json={"name": "Eggs", "quantity": 6}, headers=home_headers)
    
    # 2. Add "Eggs" via receipt
    payload = {
        "chain": "osher_ad",
        "items": [{"name": "Eggs", "quantity": 12, "location": "FRIDGE"}]
    }
    await client.post("/stock/add-receipt", json=payload, headers=home_headers)
    
    # 3. Verify
    response = await client.get("/stock/filter", params={"query": "Eggs"}, headers=home_headers)
    data = response.json()["data"][0]
    assert data["total_quantity"] == 18
    assert len(data["items"]) == 2

async def test_add_receipt_skips_unknown_product(client, home_headers):
    """Scenario: Verify 'Unknown Product' entries are ignored as per business logic."""
    payload = {
        "chain": "ramy_levy",
        "items": [
            {"name": "Milk", "quantity": 1},
            {"name": "Unknown Product", "quantity": 5}
        ]
    }
    response = await client.post("/stock/add-receipt", json=payload, headers=home_headers)
    
    assert response.status_code == 200
    assert response.json()["data"]["added_count"] == 1
    
    # Verify "Unknown Product" is not in stock
    all_res = await client.get("/stock/all", headers=home_headers)
    names = [p["original_name"] for p in all_res.json()["data"]]
    assert "Unknown Product" not in names

async def test_add_receipt_weighted_items(client, home_headers):
    """Scenario: Handle items with non-integer quantities from receipt (e.g., meat/veg)."""
    payload = {
        "chain": "victory",
        "items": [
            {"name": "Chicken", "quantity": 1, "unit": "KG", "location": "FREEZER", "weight": 1.75, "barcode": "7290000000001"}
        ]
    }
    response = await client.post("/stock/add-receipt", json=payload, headers=home_headers)
    assert response.status_code == 200
    
    # StockService casts it to int (ensuring at least 1)
    get_res = await client.get("/stock/filter", params={"query": "Chicken"}, headers=home_headers)
    assert get_res.json()["data"][0]["total_quantity"] == 1

async def test_scan_receipt_success(client, home_headers):
    """Scenario: Mocking the ML scanner and verifying API response."""
    # Mocking the scanner's parse_receipt method
    mock_scanned_items = {"12345": (2.0, "unit"), "67890": (1.0, "unit")}
    
    with patch("src.infrastructure.scanner.receipt_scanner.ReceiptScanner.parse_receipt") as mock_parse:
        mock_parse.return_value = ("mock_chain", mock_scanned_items)
        
        # We need to provide a fake file
        files = {"files": ("receipt.jpg", b"fake-image-content", "image/jpeg")}
        response = await client.post("/stock/scan", files=files, headers=home_headers)
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["chain"] == "mock_chain"
        assert len(data["items"]) == 2

# ==========================================
# 4. Error Handling
# ==========================================

async def test_add_product_missing_home_header(client, active_home):
    """
    Scenario: User is authenticated (via active_home fixture) 
              but forgets the X-Home-ID header.
    Verify: FastAPI returns 422 Unprocessable Entity.
    """
    # Act: We call the endpoint WITHOUT home_headers
    payload = {"name": "Milk", "quantity": 1}
    response = await client.post("/stock/add", json=payload)
    
    # Assert:
    # 422 = The security passed (thanks to active_home), 
    # but the Header requirement failed.
    assert response.status_code == 422

async def test_add_receipt_unauthorized_home(client, active_home):
    """Scenario: User authenticated but trying to post to a random UUID home."""
    import uuid
    bad_headers = {"X-Home-ID": str(uuid.uuid4())}
    payload = {"chain": "test", "items": [{"name": "Milk", "quantity": 1}]}
    
    response = await client.post("/stock/add-receipt", json=payload, headers=bad_headers)
    
    # Should fail with 400 (as per StockService._check_access raising ValueError)
    assert response.status_code == 400