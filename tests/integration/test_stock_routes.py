import pytest
from datetime import date
from fastapi.testclient import TestClient
from src.main import app
from src.infrastructure.app_container import AppContainer

client = TestClient(app)

# --- Fixtures ---

@pytest.fixture(autouse=True)
def reset_database():
    """
    Clears all in-memory repositories before every test.
    This ensures a clean slate and prevents test pollution.
    """
    # Clear Users
    user_repo = AppContainer.get_user_repository()
    if hasattr(user_repo, "_users"):
        user_repo._users = {}
        
    # Clear Homes
    home_repo = AppContainer.get_home_repository()
    if hasattr(home_repo, "_homes"):
        home_repo._homes = {}
        
    # Clear Products
    product_repo = AppContainer.get_product_repository()
    if hasattr(product_repo, "_products"):
        product_repo._products = {}
        
    yield

# --- Helper Functions ---

def setup_user_and_home(client):
    """
    Helper function to:
    1. Register a user
    2. Login the user
    3. Create a home
    Returns: (access_token, home_id_str)
    """
    # 1. Register
    email = "stock_test@test.com"
    password = "Password123!"
    client.post("/auth/register", json={"email": email, "password": password, "name": "Stock User"})
    
    # 2. Login
    login_res = client.post("/auth/login", json={"email": email, "password": password})
    token = login_res.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Create Home
    home_res = client.post("/homes/create", json={"name": "My Kitchen"}, headers=auth_headers)
    home_id = home_res.json()["data"]["id"]
    
    return token, home_id

# --- Tests ---

def test_add_product_success():
    """
    Test adding a new product with all required fields.
    """
    token, home_id = setup_user_and_home(client)
    headers = {"Authorization": f"Bearer {token}", "X-Home-ID": home_id}
    
    payload = {
        "name": "Milk",
        "quantity": 2,
        "barcode": "123456",
        "expiration_date": str(date.today()),
        "location": "FRIDGE",
        "nickname": "Soy Milk"
    }
    
    response = client.post("/stock/add", json=payload, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["original_name"] == "Milk"
    assert data["data"]["nickname"] == "Soy Milk"
    # Check that the expiration date was flattened correctly in the DTO
    assert data["data"]["items"][0]["quantity"] == 2

def test_add_product_missing_home_header():
    """
    Test that the request fails if X-Home-ID header is missing.
    """
    token, _ = setup_user_and_home(client)
    headers = {"Authorization": f"Bearer {token}"} # Missing X-Home-ID
    
    payload = {"name": "Milk", "quantity": 1}
    
    response = client.post("/stock/add", json=payload, headers=headers)
    
    # FastAPI automatically handles missing headers with 422 Unprocessable Entity
    assert response.status_code == 422

def test_update_quantity_success():
    """
    Test adding a product and then updating its quantity.
    """
    token, home_id = setup_user_and_home(client)
    headers = {"Authorization": f"Bearer {token}", "X-Home-ID": home_id}
    today_str = str(date.today())

    # 1. Add Product
    add_res = client.post("/stock/add", json={
        "name": "Eggs", "quantity": 12, "expiration_date": today_str
    }, headers=headers)
    product_id = add_res.json()["data"]["id"]
    
    # 2. Update Quantity (Reduce to 6)
    update_payload = {
        "expiration_date": today_str,
        "new_quantity": 6
    }
    
    response = client.patch(f"/stock/{product_id}/quantity", json=update_payload, headers=headers)
    
    assert response.status_code == 200
    # Check that quantity updated in the response
    assert response.json()["data"]["quantity"] == 6

def test_update_nickname():
    """
    Test updating a product's nickname.
    """
    token, home_id = setup_user_and_home(client)
    headers = {"Authorization": f"Bearer {token}", "X-Home-ID": home_id}
    
    # 1. Add Product
    add_res = client.post("/stock/add", json={"name": "Coke", "quantity": 1}, headers=headers)
    product_id = add_res.json()["data"]["id"]
    
    # 2. Update Nickname
    response = client.patch(f"/stock/{product_id}/nickname", json={"nickname": "Zero"}, headers=headers)
    
    assert response.status_code == 200
    assert response.json()["data"]["nickname"] == "Zero"

def test_remove_product_fully():
    """
    Test removing a product completely (quantity becomes 0).
    Note: DELETE requests pass parameters in the Query String.
    """
    token, home_id = setup_user_and_home(client)
    headers = {"Authorization": f"Bearer {token}", "X-Home-ID": home_id}
    today_str = str(date.today())
    
    # 1. Add Product
    add_res = client.post("/stock/add", json={
        "name": "Apple", "quantity": 1, "expiration_date": today_str
    }, headers=headers)
    product_id = add_res.json()["data"]["id"]
    
    # 2. Remove Product
    # Passing expiration_date as a query parameter
    response = client.delete(f"/stock/{product_id}", params={"expiration_date": today_str}, headers=headers)
    
    assert response.status_code == 200
    assert response.json()["message"] == "Product completely removed"
    assert response.json()["data"] is None

def test_search_products():
    """
    Test searching for a product by name.
    """
    token, home_id = setup_user_and_home(client)
    headers = {"Authorization": f"Bearer {token}", "X-Home-ID": home_id}
    
    # Add two products
    client.post("/stock/add", json={"name": "Green Tea", "quantity": 1}, headers=headers)
    client.post("/stock/add", json={"name": "Black Coffee", "quantity": 1}, headers=headers)
    
    # Search for "Tea"
    response = client.get("/stock/search", params={"query": "Tea"}, headers=headers)
    
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["original_name"] == "Green Tea"

def test_filter_by_location():
    """
    Test filtering products by storage location.
    """
    token, home_id = setup_user_and_home(client)
    headers = {"Authorization": f"Bearer {token}", "X-Home-ID": home_id}
    
    # Add products in different locations
    client.post("/stock/add", json={"name": "Ice Cream", "quantity": 1, "location": "FREEZER"}, headers=headers)
    client.post("/stock/add", json={"name": "Bread", "quantity": 1, "location": "PANTRY"}, headers=headers)
    
    # Filter for FREEZER
    response = client.get("/stock/filter/location", params={"location": "FREEZER"}, headers=headers)
    
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["original_name"] == "Ice Cream"