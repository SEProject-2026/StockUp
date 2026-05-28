import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, patch

# ==========================================
# 1. Lifecycle & Item Management
# ==========================================

async def test_create_shopping_list_api(client, active_home):
    """Scenario: Create a new list using the active_home context."""
    payload = {"home_id": str(active_home.id), "name": "Weekend BBQ"}
    response = await client.post("/shopping-lists/", json=payload)

    assert response.status_code == 201
    assert response.json()["data"]["name"] == "Weekend BBQ"

async def test_add_item_and_update_quantity(client, active_home):
    """Scenario: Add an item and then change its quantity."""
    # 1. Create List
    list_res = await client.post("/shopping-lists/", json={"home_id": str(active_home.id), "name": "Groceries"})
    list_id = list_res.json()["data"]["id"]

    # 2. Add Item
    await client.post(f"/shopping-lists/{list_id}/items", json={"item_name": "Steak", "quantity": 2})

    # 3. Update Quantity
    patch_res = await client.patch(f"/shopping-lists/{list_id}/items/Steak/quantity", json={"new_quantity": 5})
    
    assert patch_res.status_code == 200
    items = patch_res.json()["data"]["items"]
    assert next(i for i in items if i["item_name"] == "Steak")["quantity"] == 5

def test_get_home_lists_success(client, active_home):
    """Scenario: Retrieve all shopping lists for a home."""
    # Create two lists
    client.post("/shopping-lists/", json={"home_id": str(active_home.id), "name": "List 1"})
    client.post("/shopping-lists/", json={"home_id": str(active_home.id), "name": "List 2"})

    response = client.get(f"/shopping-lists/home/{active_home.id}")
    
    assert response.status_code == 200
    assert len(response.json()["data"]) == 2

def test_get_single_list_success(client, active_home):
    """Scenario: Retrieve a specific list by ID."""
    list_res = client.post("/shopping-lists/", json={"home_id": str(active_home.id), "name": "My List"})
    list_id = list_res.json()["data"]["id"]

    response = client.get(f"/shopping-lists/{list_id}")
    
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "My List"

def test_remove_item_from_list(client, active_home):
    """Scenario: Remove a specific item from the list."""
    list_res = client.post("/shopping-lists/", json={"home_id": str(active_home.id), "name": "Remove Test"})
    list_id = list_res.json()["data"]["id"]
    client.post(f"/shopping-lists/{list_id}/items", json={"item_name": "Apple", "quantity": 1})

    response = client.delete(f"/shopping-lists/{list_id}/items/Apple")
    
    assert response.status_code == 200
    assert len(response.json()["data"]["items"]) == 0

# ==========================================
# 2. Shopping Mode Logic
# ==========================================

async def test_full_shopping_mode_flow(client, active_home):
    """Scenario: Enter mode -> Check item -> Exit mode with clear=True."""
    # Setup list with 2 items
    list_res = await client.post("/shopping-lists/", json={"home_id": str(active_home.id), "name": "Store"})
    list_id = list_res.json()["data"]["id"]
    await client.post(f"/shopping-lists/{list_id}/items", json={"item_name": "Milk", "quantity": 1})
    await client.post(f"/shopping-lists/{list_id}/items", json={"item_name": "Bread", "quantity": 1})

    # 1. Enter Mode
    await client.post(f"/shopping-lists/{list_id}/enter-mode")
    
    # 2. Check Milk
    await client.patch(f"/shopping-lists/{list_id}/items/Milk/check")
    
    # 3. Exit with Clear
    response = await client.post(f"/shopping-lists/{list_id}/exit-mode", json={"clear": True})
    
    assert response.status_code == 200
    final_items = response.json()["data"]["items"]
    assert len(final_items) == 1
    assert final_items[0]["item_name"] == "Bread"
    assert response.json()["data"]["is_active_shopping_mode"] is False

async def test_exit_mode_without_clear(client, active_home):
    """Scenario: Exit mode but keep bought items in the list."""
    list_res = await client.post("/shopping-lists/", json={"home_id": str(active_home.id), "name": "Keep Items"})
    list_id = list_res.json()["data"]["id"]
    await client.post(f"/shopping-lists/{list_id}/items", json={"item_name": "Milk", "quantity": 1})
    await client.patch(f"/shopping-lists/{list_id}/items/Milk/check")

    # Exit with clear=False
    response = await client.post(f"/shopping-lists/{list_id}/exit-mode", json={"clear": False})
    
    assert response.status_code == 200
    assert len(response.json()["data"]["items"]) == 1
    assert response.json()["data"]["items"][0]["is_bought"] is True

# ==========================================
# 3. Recommendations (Mocked)
# ==========================================

async def test_get_recommendations_api(client, active_home):
    """Scenario: Verify recommendations route is working with a mock service."""
    list_res = await client.post("/shopping-lists/", json={"home_id": str(active_home.id), "name": "Recs"})
    list_id = list_res.json()["data"]["id"]

    mock_data = ["Apples", "Bananas"]
    with patch("src.infrastructure.app_container.AppContainer.get_recommendation_service") as mock_factory:
        mock_service = AsyncMock()
        mock_service.get_recommendations.return_value = mock_data
        mock_factory.return_value = mock_service

        response = await client.get(f"/shopping-lists/{list_id}/recommendations")
        assert response.status_code == 200
        assert response.json()["data"] == mock_data

# ==========================================
# 4. Security & Edge Cases
# ==========================================

def test_create_list_in_wrong_home_fails(client, db_session, auth_user):
    """Scenario: User tries to create a list in a home they don't belong to."""
    from tests.factories import create_user_entity, create_home_entity
    
    # Setup: auth_user exists but we create a home for someone else
    create_user_entity(db=db_session, user_id=auth_user)
    other_owner = create_user_entity(db=db_session, email="other@test.com")
    other_home = create_home_entity(db=db_session, admin_user_id=other_owner.id)
    db_session.commit()

    payload = {"home_id": str(other_home.id), "name": "Hacker List"}
    response = client.post("/shopping-lists/", json=payload)

    # Assert: Should be Forbidden or Bad Request based on your service logic
    assert response.status_code in [403, 400]

def test_shopping_routes_unauthenticated_fails(client):
    """Security: Verify unauthenticated users are blocked."""
    # Using client WITHOUT auth setup
    response = client.post("/shopping-lists/", json={"home_id": str(uuid4()), "name": "Hacker List"})
    assert response.status_code == 401

def test_interact_with_non_existent_list_fails_404(client, auth_user):
    """Sad Path: Trying to get or modify a list that doesn't exist."""
    fake_id = str(uuid4())
    
    # Check GET
    res_get = client.get(f"/shopping-lists/{fake_id}")
    assert res_get.status_code == 404

    # Check Add Item
    res_add = client.post(f"/shopping-lists/{fake_id}/items", json={"item_name": "Milk", "quantity": 1})
    assert res_add.status_code == 404

def test_delete_shopping_list_success(client, active_home):
    """Scenario: Delete a list successfully (expects 204 No Content)."""
    list_res = client.post("/shopping-lists/", json={"home_id": str(active_home.id), "name": "To Be Deleted"})
    list_id = list_res.json()["data"]["id"]

    response = client.delete(f"/shopping-lists/{list_id}")
    
    assert response.status_code == 204
    # No json() assertion here because 204 means no body!

# ==========================================
# 5. Full Router Exception Coverage (Boost to 100%)
# ==========================================

@pytest.mark.parametrize("method, endpoint, payload", [
    ("GET", f"/shopping-lists/{uuid4()}", None),
    ("POST", f"/shopping-lists/{uuid4()}/items", {"item_name": "Milk", "quantity": 1}),
    ("GET", f"/shopping-lists/{uuid4()}/recommendations", None),
    ("DELETE", f"/shopping-lists/{uuid4()}/items/Milk", None),
    ("PATCH", f"/shopping-lists/{uuid4()}/items/Milk/quantity", {"new_quantity": 2}),
    ("POST", f"/shopping-lists/{uuid4()}/enter-mode", None),
    ("PATCH", f"/shopping-lists/{uuid4()}/items/Milk/check", None),
    ("POST", f"/shopping-lists/{uuid4()}/exit-mode", {"clear": True}),
])
def test_all_shopping_routes_value_error_returns_404(client, active_home, method, endpoint, payload):
    """Coverage: Ensure EVERY shopping route properly catches ValueError and returns 404."""
    with patch("src.infrastructure.app_container.AppContainer.get_shopping_list_service") as mock_factory:
        mock_svc = AsyncMock()
        # Make all methods throw ValueError
        mock_svc.get_shopping_list.side_effect = ValueError("Not found")
        mock_svc.add_item_to_list.side_effect = ValueError("Not found")
        mock_svc.remove_item_from_list.side_effect = ValueError("Not found")
        mock_svc.update_item_quantity.side_effect = ValueError("Not found")
        mock_svc.enter_shopping_mode.side_effect = ValueError("Not found")
        mock_svc.check_item_as_bought.side_effect = ValueError("Not found")
        mock_svc.exit_shopping_mode.side_effect = ValueError("Not found")
        
        mock_factory.return_value = mock_svc
        
        # Mocking the recommendation service just in case the endpoint hits it
        with patch("src.infrastructure.app_container.AppContainer.get_recommendation_service") as rec_factory:
            rec_svc = AsyncMock()
            rec_svc.get_recommendations.side_effect = ValueError("Not found")
            rec_factory.return_value = rec_svc

            # Execute the request dynamically
            if method == "POST":
                res = client.post(endpoint, json=payload)
            elif method == "PATCH":
                res = client.patch(endpoint, json=payload)
            elif method == "DELETE":
                res = client.delete(endpoint)
            else:
                res = client.get(endpoint)

            assert res.status_code == 404
            assert "detail" in res.json()


def test_create_list_general_exception_returns_400(client, active_home):
    """Coverage: Ensure create_list catches general Exceptions and returns 400."""
    with patch("src.infrastructure.app_container.AppContainer.get_management_service") as mock_mgt:
        # Bypass management check
        mock_mgt.return_value = AsyncMock()
        
        with patch("src.infrastructure.app_container.AppContainer.get_shopping_list_service") as mock_shop:
            mock_shop_svc = AsyncMock()
            # Throw a general exception
            mock_shop_svc.create_shopping_list.side_effect = Exception("DB Timeout")
            mock_shop.return_value = mock_shop_svc
            
            res = client.post("/shopping-lists/", json={"home_id": str(active_home.id), "name": "Test"})
            
            assert res.status_code == 400