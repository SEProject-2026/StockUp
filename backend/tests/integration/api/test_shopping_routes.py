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

# def test_create_list_in_wrong_home_fails(client, db_session, auth_user):
#     """Scenario: User tries to create a list in a home they don't belong to."""
#     from tests.factories import create_user_entity, create_home_entity
    
#     # Setup: auth_user exists but we create a home for someone else
#     create_user_entity(db=db_session, user_id=auth_user)
#     other_owner = create_user_entity(db=db_session, email="other@test.com")
#     other_home = create_home_entity(db=db_session, admin_user_id=other_owner.id)
#     db_session.commit()

#     payload = {"home_id": str(other_home.id), "name": "Hacker List"}
#     response = client.post("/shopping-lists/", json=payload)

#     # Assert: Should be Forbidden or Bad Request based on your service logic
#     assert response.status_code in [403, 400]

# def test_delete_non_existent_list_fails(client, active_home):
#     """Scenario: Deleting a UUID that doesn't exist."""
#     random_id = uuid4()
#     response = client.delete(f"/shopping-lists/{random_id}")
#     # Depend on your service, but shouldn't be 204
#     assert response.status_code in [404, 400]