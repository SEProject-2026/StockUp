from uuid import uuid4

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

def test_update_item_location_success(client, home_headers):
    """Scenario: Move an item to a different location."""
    add_res = client.post("/stock/add", json={"name": "Fish", "quantity": 1, "location": "FRIDGE"}, headers=home_headers)
    p_id = add_res.json()["data"]["id"]
    i_id = add_res.json()["data"]["items"][0]["id"]
    
    response = client.patch(
        f"/stock/{p_id}/items/{i_id}/location", 
        json={"location": "FREEZER"}, 
        headers=home_headers
    )
    
    assert response.status_code == 200
    assert response.json()["data"]["items"][0]["location"] == "FREEZER"

def test_update_nickname_success(client, home_headers):
    """Scenario: Update the nickname of a product."""
    add_res = client.post("/stock/add", json={"name": "Water", "quantity": 6}, headers=home_headers)
    p_id = add_res.json()["data"]["id"]
    
    response = client.patch(
        f"/stock/{p_id}/nickname", 
        json={"nickname": "Mineral Water"}, 
        headers=home_headers
    )
    
    assert response.status_code == 200
    assert response.json()["data"]["nickname"] == "Mineral Water"

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

def test_search_global_catalog_by_name(client, home_headers):
    """Scenario: Search catalog by name string."""
    with patch("src.infrastructure.app_container.AppContainer.get_stock_service") as mock_factory:
        mock_svc = AsyncMock()
        mock_item = CatalogItem(barcode="111", name="Test Milk", manufacturer="Tnuva")
        mock_svc.search_product_by_name_external_db.return_value = [mock_item]
        mock_factory.return_value = mock_svc
        
        response = client.get("/stock/catalog/search?query=Milk", headers=home_headers)
        
        assert response.status_code == 200
        assert len(response.json()["data"]) == 1
        assert response.json()["data"][0]["name"] == "Test Milk"

def test_scan_receipt_file_upload(client, home_headers):
    """Scenario: Uploading a file to the scan endpoint."""
    with patch("src.infrastructure.app_container.AppContainer.get_stock_service") as mock_factory:
        mock_svc = AsyncMock()
        # Mocking the service return to bypass actual ML execution during API test
        from src.domain.receipt.receipt import ReceiptDTO
        mock_svc.scan_receipt.return_value = ReceiptDTO(
            id=uuid4(), home_id=uuid4(), user_id=uuid4(), chain="Test Chain", items=[]
        )
        mock_factory.return_value = mock_svc

        # Prepare fake file payload for TestClient
        files = [("files", ("receipt.jpg", b"fake_image_content", "image/jpeg"))]
        
        # We extract just the X-Home-ID. 
        # WARNING: We must NOT send "Content-Type: application/json" because uploading files uses "multipart/form-data"
        headers = {"X-Home-ID": home_headers["X-Home-ID"]}
        
        response = client.post("/stock/scan", files=files, headers=headers)
        
        assert response.status_code == 200
        assert response.json()["data"]["chain"] == "Test Chain"

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

def test_stock_item_not_found_returns_400(client, home_headers):
    """Sad Path: Trying to update a completely fake product/item ID."""
    fake_p_id = str(uuid4())
    fake_i_id = str(uuid4())
    
    response = client.patch(
        f"/stock/{fake_p_id}/items/{fake_i_id}/quantity", 
        json={"new_quantity": 5}, 
        headers=home_headers
    )
    
    # The service will throw a ValueError ("Product not found"), which the router turns into a 400
    assert response.status_code == 400
    assert "detail" in response.json()

def test_stock_routes_unauthenticated_fails(client):
    """Security: Verify unauthenticated users are blocked from stock management."""
    headers = {"X-Home-ID": str(uuid4())}
    
    response = client.get("/stock/all", headers=headers)
    
    assert response.status_code == 401

# ==========================================
# 5. Full Router Exception Coverage (Boost to 100%)
# ==========================================

@pytest.mark.parametrize("method, endpoint, payload", [
    ("POST", "/stock/add", {"name": "Valid Name", "quantity": 1, "barcode": "123"}),    ("PATCH", f"/stock/{uuid4()}/items/{uuid4()}/expiration", {"new_date": "2026-01-01"}),
    ("PATCH", f"/stock/{uuid4()}/items/{uuid4()}/location", {"location": "FREEZER"}),
    ("PATCH", f"/stock/{uuid4()}/nickname", {"nickname": "New Name"}),
    ("DELETE", f"/stock/{uuid4()}/items/{uuid4()}", None),
    ("GET", "/stock/filter?query=Milk", None),
    ("GET", "/stock/all", None),
    ("GET", "/stock/catalog/search?query=Milk", None),
    ("GET", f"/stock/catalog/barcode/12345", None),
    ("POST", "/stock/add-receipt", {"chain": "test", "items": []})
])
def test_all_stock_routes_value_error_returns_400(client, home_headers, method, endpoint, payload):
    """Coverage: Ensure EVERY route properly catches ValueError from the Domain/Service and returns 400."""
    with patch("src.infrastructure.app_container.AppContainer.get_stock_service") as mock_factory:
        mock_svc = AsyncMock()
        # Make ALL methods of the mock throw ValueError to simulate Domain validation failures
        mock_svc.add_product.side_effect = ValueError("Domain error")
        mock_svc.update_item_date.side_effect = ValueError("Domain error")
        mock_svc.update_item_location.side_effect = ValueError("Domain error")
        mock_svc.update_nickname.side_effect = ValueError("Domain error")
        mock_svc.remove_item.side_effect = ValueError("Domain error")
        mock_svc.filter_products.side_effect = ValueError("Domain error")
        mock_svc.get_home_products.side_effect = ValueError("Domain error")
        mock_svc.search_product_by_name_external_db.side_effect = ValueError("Domain error")
        mock_svc.search_product_by_barcode_external_db.side_effect = ValueError("Domain error")
        mock_svc.add_receipt.side_effect = ValueError("Domain error")
        mock_svc.validate_receipt.side_effect = ValueError("Domain error")
        
        mock_factory.return_value = mock_svc

        # Execute the correct HTTP method dynamically
        if method == "POST":
            res = client.post(endpoint, json=payload, headers=home_headers)
        elif method == "PATCH":
            res = client.patch(endpoint, json=payload, headers=home_headers)
        elif method == "DELETE":
            res = client.delete(endpoint, headers=home_headers)
        else:
            res = client.get(endpoint, headers=home_headers)

        assert res.status_code == 400
        assert "detail" in res.json()


def test_stock_scan_receipt_internal_error_500(client, home_headers):
    """Coverage: Ensure scan_receipt catches general Exceptions and returns 500."""
    with patch("src.infrastructure.app_container.AppContainer.get_stock_service") as mock_factory:
        mock_svc = AsyncMock()
        mock_svc.scan_receipt.side_effect = Exception("ML Model Crashed")
        mock_factory.return_value = mock_svc

        files = [("files", ("receipt.jpg", b"fake_image_content", "image/jpeg"))]
        headers = {"X-Home-ID": home_headers["X-Home-ID"]}
        res = client.post("/stock/scan", files=files, headers=headers)

        assert res.status_code == 500
        assert "ML Model Crashed" in res.json()["detail"]


def test_stock_add_receipt_internal_error_500(client, home_headers):
    """Coverage: Ensure add_receipt catches general Exceptions and returns 500."""
    with patch("src.infrastructure.app_container.AppContainer.get_stock_service") as mock_factory:
        mock_svc = AsyncMock()
        mock_svc.validate_receipt.side_effect = Exception("DB Connection Lost")
        mock_factory.return_value = mock_svc

        payload = {"chain": "test", "items": []}
        res = client.post("/stock/add-receipt", json=payload, headers=home_headers)

        assert res.status_code == 500
        assert "DB Connection Lost" in res.json()["detail"]


def test_get_global_product_by_barcode_not_found_returns_200_with_none(client, home_headers):
    """Coverage: Test the 'if not item:' branch in barcode lookup."""
    with patch("src.infrastructure.app_container.AppContainer.get_stock_service") as mock_factory:
        mock_svc = AsyncMock()
        # Service successfully searched but found nothing (returns None)
        mock_svc.search_product_by_barcode_external_db.return_value = None
        mock_factory.return_value = mock_svc

        res = client.get("/stock/catalog/barcode/999999", headers=home_headers)

        assert res.status_code == 200
        assert res.json()["data"] is None
        assert "not found" in res.json()["message"]
def test_add_receipt_unauthorized_home(client, active_home):
    """Scenario: User authenticated but trying to post to a random UUID home."""
    import uuid
    bad_headers = {"X-Home-ID": str(uuid.uuid4())}
    payload = {"chain": "test", "items": [{"name": "Milk", "quantity": 1}]}
    
    response = await client.post("/stock/add-receipt", json=payload, headers=bad_headers)
    
    assert response.status_code == 400
