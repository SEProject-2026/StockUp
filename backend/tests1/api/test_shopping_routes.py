import pytest
from uuid import uuid4, UUID
from tests1.container import testing_container
from src.domain.enums import LocationType

# --- Setup & Reset ---

def setup_function():
    """Reset state before every test to ensure isolation."""
    testing_container.reset_state()

# --- Auth & Context Helpers ---

def get_auth_headers(email: str, name: str):
    pwd = "Password123!"
    testing_container.client.post("/auth/register", json={
        "email": email, "password": pwd, "password_confirm": pwd, "name": name
    })
    login_res = testing_container.client.post("/auth/login", json={"email": email, "password": pwd})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def create_home_helper(headers, name="Test Home"):
    res = testing_container.client.post("/homes/create", json={"name": name}, headers=headers)
    return res.json()["data"]

# --- Shopping List API Tests ---

@pytest.mark.asyncio
async def test_create_shopping_list_flow():
    """Scenario: Authenticated user creates a list for their home."""
    headers = get_auth_headers("shopper@test.com", "Buyer")
    home = create_home_helper(headers)
    home_id = home["id"]

    # Act: Create List
    payload = {"home_id": home_id, "name": "Weekend BBQ"}
    response = testing_container.client.post("/shopping-lists/", json=payload, headers=headers)

    # Assert
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["name"] == "Weekend BBQ"
    assert data["home_id"] == home_id
    assert "id" in data

@pytest.mark.asyncio
async def test_add_item_to_list_api():
    """Scenario: User adds an item to a specific list via API."""
    headers = get_auth_headers("user@test.com", "User")
    home_id = create_home_helper(headers)["id"]
    
    # 1. Create List
    list_res = testing_container.client.post("/shopping-lists/", json={"home_id": home_id, "name": "Groceries"}, headers=headers)
    list_id = list_res.json()["data"]["id"]

    # 2. Act: Add Item
    item_payload = {
        "item_name": "Steak",
        "quantity": 2,
        "location": LocationType.FRIDGE
    }
    add_res = testing_container.client.post(f"/shopping-lists/{list_id}/items", json=item_payload, headers=headers)

    # 3. Assert
    assert add_res.status_code == 200
    items = add_res.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["item_name"] == "Steak"
    assert items[0]["quantity"] == 2

@pytest.mark.asyncio
async def test_check_item_and_exit_mode_flow():
    """Scenario: Full shopping flow: add item -> check bought -> exit mode with clear."""
    headers = get_auth_headers("buyer@test.com", "Buyer")
    home_id = create_home_helper(headers)["id"]
    
    # Setup: List with 2 items
    list_id = testing_container.client.post("/shopping-lists/", json={"home_id": home_id, "name": "Store"}, headers=headers).json()["data"]["id"]
    testing_container.client.post(f"/shopping-lists/{list_id}/items", json={"item_name": "Milk", "quantity": 1}, headers=headers)
    testing_container.client.post(f"/shopping-lists/{list_id}/items", json={"item_name": "Bread", "quantity": 1}, headers=headers)

    # 1. Check Milk as bought
    check_res = testing_container.client.patch(f"/shopping-lists/{list_id}/items/Milk/check", headers=headers)
    assert check_res.status_code == 200
    
    # 2. Exit shopping mode with clear=True
    exit_res = testing_container.client.post(f"/shopping-lists/{list_id}/exit-mode", json={"clear": True}, headers=headers)
    
    # 3. Assert: Only Bread remains
    assert exit_res.status_code == 200
    final_items = exit_res.json()["data"]["items"]
    assert len(final_items) == 1
    assert final_items[0]["item_name"] == "Bread"

@pytest.mark.asyncio
async def test_get_home_lists_api():
    """Scenario: Fetch all lists belonging to a home."""
    headers = get_auth_headers("multi@test.com", "User")
    home_id = create_home_helper(headers)["id"]
    
    # Create 2 lists
    testing_container.client.post("/shopping-lists/", json={"home_id": home_id, "name": "List 1"}, headers=headers)
    testing_container.client.post("/shopping-lists/", json={"home_id": home_id, "name": "List 2"}, headers=headers)

    # Act
    response = testing_container.client.get(f"/shopping-lists/home/{home_id}", headers=headers)

    # Assert
    assert response.status_code == 200
    assert len(response.json()["data"]) == 2

@pytest.mark.asyncio
async def test_delete_list_api():
    """Scenario: Delete a list through the API."""
    headers = get_auth_headers("delete@test.com", "User")
    home_id = create_home_helper(headers)["id"]
    list_id = testing_container.client.post("/shopping-lists/", json={"home_id": home_id, "name": "Temp"}, headers=headers).json()["data"]["id"]

    # Act
    del_res = testing_container.client.delete(f"/shopping-lists/{list_id}", headers=headers)
    assert del_res.status_code == 204 # No Content

    # Verify gone
    get_res = testing_container.client.get(f"/shopping-lists/{list_id}", headers=headers)
    assert get_res.status_code == 404