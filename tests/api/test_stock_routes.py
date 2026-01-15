from datetime import date
from unittest.mock import AsyncMock, patch
from src.repositories.catalog_provider import CatalogItem
from tests.container import testing_container

def setup_function():
    testing_container.reset_state()

def setup_user_and_home():
    email = "stock_test@test.com"
    password = "Password123!"
    testing_container.client.post("/auth/register", json={"email": email, "password": password, "password_confirm": password, "name": "Stock User"})
    
    login_res = testing_container.client.post("/auth/login", json={"email": email, "password": password})
    token = login_res.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}
    
    home_res = testing_container.client.post("/homes/create", json={"name": "My Kitchen"}, headers=auth_headers)
    home_id = home_res.json()["data"]["id"]
    
    return token, home_id

def test_add_product_success():
    token, home_id = setup_user_and_home()
    headers = {"Authorization": f"Bearer {token}", "X-Home-ID": home_id}
    
    payload = {
        "name": "Milk",
        "quantity": 2,
        "barcode": "123456",
        "expiration_date": str(date.today()),
        "location": "FRIDGE",
        "nickname": "Soy Milk"
    }
    
    response = testing_container.client.post("/stock/add", json=payload, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["original_name"] == "Milk"
    assert data["data"]["nickname"] == "Soy Milk"
    assert data["data"]["items"][0]["quantity"] == 2

def test_add_product_missing_home_header():
    token, _ = setup_user_and_home()
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {"name": "Milk", "quantity": 1}
    
    response = testing_container.client.post("/stock/add", json=payload, headers=headers)
    
    assert response.status_code == 422

def test_update_quantity_success():
    token, home_id = setup_user_and_home()
    headers = {"Authorization": f"Bearer {token}", "X-Home-ID": home_id}
    today_str = str(date.today())

    add_res = testing_container.client.post("/stock/add", json={
        "name": "Eggs", "quantity": 12, "expiration_date": today_str
    }, headers=headers)
    product_id = add_res.json()["data"]["id"]
    
    update_payload = {
        "expiration_date": today_str,
        "new_quantity": 6
    }
    
    response = testing_container.client.patch(f"/stock/{product_id}/quantity", json=update_payload, headers=headers)
    
    assert response.status_code == 200
    assert response.json()["data"]["quantity"] == 6

def test_update_nickname():
    token, home_id = setup_user_and_home()
    headers = {"Authorization": f"Bearer {token}", "X-Home-ID": home_id}
    
    add_res = testing_container.client.post("/stock/add", json={"name": "Coke", "quantity": 1}, headers=headers)
    product_id = add_res.json()["data"]["id"]
    
    response = testing_container.client.patch(f"/stock/{product_id}/nickname", json={"nickname": "Zero"}, headers=headers)
    
    assert response.status_code == 200
    assert response.json()["data"]["nickname"] == "Zero"

def test_remove_product_fully():
    token, home_id = setup_user_and_home()
    headers = {"Authorization": f"Bearer {token}", "X-Home-ID": home_id}
    today_str = str(date.today())
    
    add_res = testing_container.client.post("/stock/add", json={
        "name": "Apple", "quantity": 1, "expiration_date": today_str
    }, headers=headers)
    product_id = add_res.json()["data"]["id"]
    
    response = testing_container.client.delete(f"/stock/{product_id}", params={"expiration_date": today_str}, headers=headers)
    
    assert response.status_code == 200
    assert response.json()["message"] == "Product completely removed"
    assert response.json()["data"] is None

def test_search_products():
    token, home_id = setup_user_and_home()
    headers = {"Authorization": f"Bearer {token}", "X-Home-ID": home_id}
    
    testing_container.client.post("/stock/add", json={"name": "Green Tea", "quantity": 1}, headers=headers)
    testing_container.client.post("/stock/add", json={"name": "Black Coffee", "quantity": 1}, headers=headers)
    
    response = testing_container.client.get("/stock/search", params={"query": "Tea"}, headers=headers)
    
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["original_name"] == "Green Tea"

def test_filter_by_location():
    token, home_id = setup_user_and_home()
    headers = {"Authorization": f"Bearer {token}", "X-Home-ID": home_id}
    
    testing_container.client.post("/stock/add", json={"name": "Ice Cream", "quantity": 1, "location": "FREEZER"}, headers=headers)
    testing_container.client.post("/stock/add", json={"name": "Bread", "quantity": 1, "location": "PANTRY"}, headers=headers)
    
    response = testing_container.client.get("/stock/filter/location", params={"location": "FREEZER"}, headers=headers)
    
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["original_name"] == "Ice Cream"

def test_update_expiration_date():
    token, home_id = setup_user_and_home()
    headers = {"Authorization": f"Bearer {token}", "X-Home-ID": home_id}
    today_str = str(date.today())
    
    add_res = testing_container.client.post("/stock/add", json={
        "name": "Milk", "quantity": 1, "expiration_date": today_str
    }, headers=headers)
    product_id = add_res.json()["data"]["id"]
    
    new_date = "2026-12-31"
    response = testing_container.client.patch(f"/stock/{product_id}/expiration", json={
        "old_date": today_str,
        "new_date": new_date
    }, headers=headers)
    
    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert items[0]["expiration_date"] == new_date

def test_get_all_products():
    token, home_id = setup_user_and_home()
    headers = {"Authorization": f"Bearer {token}", "X-Home-ID": home_id}
    
    testing_container.client.post("/stock/add", json={"name": "Banana", "quantity": 5}, headers=headers)
    testing_container.client.post("/stock/add", json={"name": "Apple", "quantity": 3}, headers=headers)
    
    response = testing_container.client.get("/stock/all", headers=headers)
    
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 2
    
    names = [p["original_name"] for p in data]
    assert "Banana" in names
    assert "Apple" in names

def test_catalog_search_autocomplete():
    token, home_id = setup_user_and_home()
    headers = {"Authorization": f"Bearer {token}", "X-Home-ID": home_id}
    
    mock_items = [
        CatalogItem(barcode="111", name="Mock Milk 3%", manufacturer="Tnuva", chain_source="GLOBAL"),
        CatalogItem(barcode="222", name="Mock Soy Milk", manufacturer="Tnuva", chain_source="GLOBAL")
    ]
    
    # FIX: Patching "search_items_by_name" (Matches Interface)
    with patch.object(testing_container.catalog_provider, "search_items_by_name", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = mock_items
        
        response = testing_container.client.get("/stock/catalog/search", params={"query": "Milk"}, headers=headers)
        
        assert response.status_code == 200
        data = response.json()["data"]
        
        assert len(data) == 2
        assert data[0]["name"] == "Mock Milk 3%"
        assert data[0]["barcode"] == "111"

def test_catalog_barcode_lookup():
    token, home_id = setup_user_and_home()
    headers = {"Authorization": f"Bearer {token}", "X-Home-ID": home_id}
    
    mock_item = CatalogItem(barcode="7290123", name="Scanned Bamba", manufacturer="Osem")
    
    # FIX: Patching "get_item_by_barcode" (Matches Interface)
    with patch.object(testing_container.catalog_provider, "get_item_by_barcode", new_callable=AsyncMock) as mock_lookup:
        mock_lookup.return_value = mock_item
        
        response = testing_container.client.get("/stock/catalog/barcode/7290123", headers=headers)
        
        assert response.status_code == 200
        data = response.json()["data"]
        
        assert data["name"] == "Scanned Bamba"
        assert data["manufacturer"] == "Osem"





def test_add_receipt_success():
    """
    Test adding a finalized receipt with new items.
    Verifies that the endpoint returns 200
    """
    token, home_id = setup_user_and_home()
    headers = {"Authorization": f"Bearer {token}", "X-Home-ID": home_id}
    
    # 1. Prepare Payload (AddReceiptRequest)
    payload = {
        "home_id": home_id,
        "chain": "Rami Levi",
        "items": [
            {
                "barcode": "888",
                "name": "New Cheese",
                "quantity": 2,
                "unit": "UNIT",
                "location": "FRIDGE",
                "expiration_date": str(date.today())
            },
            {
                "barcode": "999",
                "name": "New Bread",
                "quantity": 1,
                "unit": "UNIT",
                "location": "PANTRY"
            }
        ]
    }
    
    # 2. Act
    response = testing_container.client.post("/stock/receipt/add", json=payload, headers=headers)
    
    # 3. Assert Response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["items_added"] == 2
    assert "receipt_id" in data["data"]
    
    # 4. Verify in "DB" (via GET /all)
    get_res = testing_container.client.get("/stock/all", headers=headers)
    products = get_res.json()["data"]
    
    # Check that "New Cheese" exists with correct quantity
    cheese = next((p for p in products if p["original_name"] == "New Cheese"), None)
    assert cheese is not None
    assert cheese["items"][0]["quantity"] == 2
    assert cheese["location"] == "FRIDGE"

def test_add_receipt_updates_existing_product():
    """
    Test that if a product already exists, the receipt adds to its quantity
    instead of creating a duplicate.
    """
    token, home_id = setup_user_and_home()
    headers = {"Authorization": f"Bearer {token}", "X-Home-ID": home_id}
    
    # 1. Setup: Manually add "Cola" first
    testing_container.client.post("/stock/add", json={
        "name": "Cola", 
        "quantity": 5, 
        "barcode": "123_COLA",
        "location": "PANTRY"
    }, headers=headers)
    
    # 2. Prepare Receipt with the SAME product
    payload = {
        "home_id": home_id,
        "items": [
            {
                "barcode": "123_COLA",
                "name": "Cola", # Matches existing name
                "quantity": 6,
                "unit": "UNIT",
                "location": "PANTRY"
            }
        ]
    }
    
    # 3. Act
    response = testing_container.client.post("/stock/receipt/add", json=payload, headers=headers)
    
    # 4. Assert
    assert response.status_code == 200
    assert response.json()["data"]["items_added"] == 1 # Added to 1 product
    
    # 5. Verify Quantity Updated (5 + 6 = 11)
    get_res = testing_container.client.get("/stock/all", headers=headers)
    products = get_res.json()["data"]
    
    cola = products[0]
    # Sum all quantity batches for this product
    total_qty = sum(item["quantity"] for item in cola["items"])
    assert total_qty == 11

def test_add_receipt_validation_error():
    """
    Test that the endpoint validates the header Home ID matches the payload Home ID.
    """
    token, home_id = setup_user_and_home()
    headers = {"Authorization": f"Bearer {token}", "X-Home-ID": home_id}
    
    # Payload with a DIFFERENT home_id (random UUID)
    wrong_home_id = "00000000-0000-0000-0000-000000000000"
    
    payload = {
        "home_id": wrong_home_id, 
        "items": [] 
    }
    
    response = testing_container.client.post("/stock/receipt/add", json=payload, headers=headers)
    
    # Expect 400 Bad Request because header mismatch
    assert response.status_code == 400
    assert "Home ID does not match" in response.json()["detail"]