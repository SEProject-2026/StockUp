from datetime import date
from unittest.mock import AsyncMock, patch
from src.repositories.catalog_provider import CatalogItem
from tests.container import testing_container

def setup_function():
    testing_container.reset_state()

def setup_user_and_home():
    """Helper to create user, home and get auth headers"""
    email = "stock_routes@test.com"
    password = "Password123!"
    
    # Register & Login
    testing_container.client.post("/auth/register", json={
        "email": email, "password": password, "password_confirm": password, "name": "Route User"
    })
    login_res = testing_container.client.post("/auth/login", json={"email": email, "password": password})
    token = login_res.json()["access_token"]
    
    # Create Home
    auth_headers = {"Authorization": f"Bearer {token}"}
    home_res = testing_container.client.post("/homes/create", json={"name": "Route Home"}, headers=auth_headers)
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
    data = response.json()["data"]
    assert data["original_name"] == "Milk"
    assert data["items"][0]["quantity"] == 2
    # Ensure item has a UUID
    assert "id" in data["items"][0]

def test_update_item_quantity_success():
    token, home_id = setup_user_and_home()
    headers = {"Authorization": f"Bearer {token}", "X-Home-ID": home_id}
    
    # 1. Add Product
    add_res = testing_container.client.post("/stock/add", json={
        "name": "Eggs", "quantity": 12
    }, headers=headers)
    
    product_data = add_res.json()["data"]
    product_id = product_data["id"]
    item_id = product_data["items"][0]["id"]
    
    # 2. Update Quantity using item_id
    update_payload = {"new_quantity": 6}
    response = testing_container.client.patch(
        f"/stock/{product_id}/items/{item_id}/quantity", 
        json=update_payload, 
        headers=headers
    )
    
    assert response.status_code == 200
    assert response.json()["data"]["items"][0]["quantity"] == 6
    assert response.json()["data"]["total_quantity"] == 6

def test_update_item_expiration_success():
    token, home_id = setup_user_and_home()
    headers = {"Authorization": f"Bearer {token}", "X-Home-ID": home_id}
    today_str = str(date.today())
    
    # 1. Add Product
    add_res = testing_container.client.post("/stock/add", json={
        "name": "Yogurt", "quantity": 1, "expiration_date": today_str
    }, headers=headers)
    
    product_data = add_res.json()["data"]
    product_id = product_data["id"]
    item_id = product_data["items"][0]["id"]
    
    # 2. Update Date
    new_date = "2026-12-31"
    response = testing_container.client.patch(
        f"/stock/{product_id}/items/{item_id}/expiration", 
        json={"new_date": new_date}, 
        headers=headers
    )
    
    assert response.status_code == 200
    assert response.json()["data"]["items"][0]["expiration_date"] == new_date

def test_update_item_location_success():
    token, home_id = setup_user_and_home()
    headers = {"Authorization": f"Bearer {token}", "X-Home-ID": home_id}
    
    # 1. Add Product to PANTRY
    add_res = testing_container.client.post("/stock/add", json={
        "name": "Canned Tuna", "quantity": 5, "location": "PANTRY"
    }, headers=headers)
    
    product_data = add_res.json()["data"]
    product_id = product_data["id"]
    item_id = product_data["items"][0]["id"]
    
    # 2. Move to FRIDGE (Opened?)
    response = testing_container.client.patch(
        f"/stock/{product_id}/items/{item_id}/location",
        json={"location": "FRIDGE"},
        headers=headers
    )
    
    assert response.status_code == 200
    
    # Verify the item location in response
    updated_item = response.json()["data"]["items"][0]
    assert updated_item["location"] == "FRIDGE"

def test_update_product_nickname():
    token, home_id = setup_user_and_home()
    headers = {"Authorization": f"Bearer {token}", "X-Home-ID": home_id}
    
    add_res = testing_container.client.post("/stock/add", json={"name": "Coke", "quantity": 1}, headers=headers)
    product_id = add_res.json()["data"]["id"]
    
    response = testing_container.client.patch(
        f"/stock/{product_id}/nickname", 
        json={"nickname": "Zero"}, 
        headers=headers
    )
    
    assert response.status_code == 200
    assert response.json()["data"]["nickname"] == "Zero"

def test_remove_item_fully_deletes_product():
    token, home_id = setup_user_and_home()
    headers = {"Authorization": f"Bearer {token}", "X-Home-ID": home_id}
    
    # 1. Add Product (1 item)
    add_res = testing_container.client.post("/stock/add", json={
        "name": "Apple", "quantity": 1
    }, headers=headers)
    
    product_data = add_res.json()["data"]
    product_id = product_data["id"]
    item_id = product_data["items"][0]["id"]
    
    # 2. Delete the item
    response = testing_container.client.delete(
        f"/stock/{product_id}/items/{item_id}", 
        headers=headers
    )
    
    assert response.status_code == 200
    assert response.json()["message"] == "Product completely removed"
    assert response.json()["data"] is None

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

def test_search_products():
    token, home_id = setup_user_and_home()
    headers = {"Authorization": f"Bearer {token}", "X-Home-ID": home_id}
    
    testing_container.client.post("/stock/add", json={"name": "Green Tea", "quantity": 1}, headers=headers)
    
    response = testing_container.client.get("/stock/search", params={"query": "Tea"}, headers=headers)
    
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["original_name"] == "Green Tea"

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





def test_add_receipt_endpoint_success():
    token, home_id = setup_user_and_home()
    headers = {"Authorization": f"Bearer {token}", "X-Home-ID": home_id}

    payload = {
        "chain": "victory", # Required field
        "items": [
            {
                "name": "Milk",
                "quantity": 2.0,
                "barcode": "111222",
                "expiration_date": str(date.today()),
                "location": "FRIDGE",
                "unit": "UNIT",
                "nickname": "Organic Milk",
                "weight": None
            },
            {
                "name": "Pasta",
                "quantity": 3.0,
                "barcode": "444555",
                "location": "PANTRY",
                "unit": "UNIT",
                "weight": None
            }
        ]
    }

    response = testing_container.client.post("/stock/add-receipt", json=payload, headers=headers)
    assert response.status_code == 200

def test_add_receipt_missing_home_header():
    """
    Scenario: User is authenticated but forgets the X-Home-ID header.
    Expected: 422 Unprocessable Entity (FastAPI header validation).
    """
    token, _ = setup_user_and_home()
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {"items": [{"name": "Milk", "quantity": 1}]}
    
    response = testing_container.client.post("/stock/add-receipt", json=payload, headers=headers)
    
    assert response.status_code == 422

def test_add_receipt_unauthorized():
    """
    Scenario: Request without a valid Bearer token.
    Expected: 401 Unauthorized.
    """
    _, home_id = setup_user_and_home()
    headers = {"X-Home-ID": home_id}
    
    payload = {"items": [{"name": "Milk", "quantity": 1}]}
    
    response = testing_container.client.post("/stock/add-receipt", json=payload, headers=headers)
    
    assert response.status_code == 401