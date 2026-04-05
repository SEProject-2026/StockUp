import pytest
from uuid import UUID
from tests.container import testing_container

def setup_function():
    testing_container.reset_state()

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

@pytest.mark.asyncio
async def test_get_recommendations_flow():
    """Scenario: User gets recommendations for their shopping list."""
    headers = get_auth_headers("rec@test.com", "User")
    home = create_home_helper(headers)
    home_id = home["id"]

    # 1. Create List
    list_res = testing_container.client.post("/shopping-lists/", json={"home_id": home_id, "name": "Groceries"}, headers=headers)
    list_id = list_res.json()["data"]["id"]

    # 2. Add an item to make it non-empty (Recommendation engine requires items)
    testing_container.client.post(f"/shopping-lists/{list_id}/items", json={"item_name": "Milk", "quantity": 1}, headers=headers)

    # 3. Act: Get Recommendations
    response = testing_container.client.get(f"/shopping-lists/{list_id}/recommendations", headers=headers)

    # 4. Assert
    assert response.status_code == 200
    data = response.json()["data"]
    assert isinstance(data, list)
