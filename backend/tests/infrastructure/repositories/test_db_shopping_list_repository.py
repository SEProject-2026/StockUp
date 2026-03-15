import pytest
from uuid import uuid4
from src.domain.shopping_list.shopping_list import ShoppingList, ShoppingListItem
from tests.container import testing_container

async def create_home_context():
    """Helper to create a home in DB for FK constraints."""
    user = await testing_container.user_service.register(
        f"repo_{uuid4().hex[:4]}@test.com", "Pass123!", "Pass123!", "Repo User"
    )
    home = await testing_container.management_service.create_home(user.id, "Integration Home")
    return home.get_id()

# --- Repository Tests ---

@pytest.mark.asyncio
async def test_db_save_and_get_list():
    """
    Scenario: Save a shopping list with JSON items and retrieve it.
    Verifies: JSON serialization/deserialization.
    """
    repo = testing_container.shopping_list_repo
    home_id = await create_home_context()
    
    # 1. Create List with Items
    new_list = ShoppingList(
        name="Market Trip",
        home_id=home_id
    )
    new_list.add_item("Apples", 5)
    new_list.add_item("Steak", 2)
    new_list.check_item_as_bought("Apples")
    
    # 2. Save to DB
    await repo.save(new_list)
    
    # 3. Retrieve from DB
    fetched = await repo.get_by_id(new_list.id)
    
    # 4. Assertions
    assert fetched is not None
    assert fetched.id == new_list.id
    assert fetched.name == "Market Trip"
    assert len(fetched.items) == 2
    
    # Verify Item Data Integrity (The JSON conversion)
    apples = next(item for item in fetched.items if item.item_name == "Apples")
    assert apples.quantity == 5
    assert apples.is_bought is True

@pytest.mark.asyncio
async def test_db_update_existing_list():
    """
    Scenario: Save a list, modify it, and save again (update).
    """
    repo = testing_container.shopping_list_repo
    home_id = await create_home_context()
    
    # 1. Initial Save
    shopping_list = ShoppingList(name="Old Name", home_id=home_id)
    await repo.save(shopping_list)
    
    # 2. Modify State
    shopping_list.name = "Updated Name"
    shopping_list.enter_shopping_mode()
    shopping_list.add_item("Milk", 1)
    
    # 3. Save (Update)
    await repo.save(shopping_list)
    
    # 4. Verify
    fetched = await repo.get_by_id(shopping_list.id)
    assert fetched.name == "Updated Name"
    assert fetched.is_active_shopping_mode is True
    assert len(fetched.items) == 1

@pytest.mark.asyncio
async def test_db_get_all_by_home():
    """
    Scenario: Verify multiple lists can be retrieved for a single home.
    """
    repo = testing_container.shopping_list_repo
    home_id = await create_home_context()
    
    # Add 2 lists
    list1 = ShoppingList(name="List 1", home_id=home_id)
    list2 = ShoppingList(name="List 2", home_id=home_id)
    
    await repo.save(list1)
    await repo.save(list2)
    
    # Fetch all
    all_lists = await repo.get_all_by_home(home_id)
    
    assert len(all_lists) == 2
    names = {lst.name for lst in all_lists}
    assert "List 1" in names
    assert "List 2" in names

@pytest.mark.asyncio
async def test_db_delete_list():
    """
    Scenario: Delete a list and ensure it's gone from DB.
    """
    repo = testing_container.shopping_list_repo
    home_id = await create_home_context()
    
    shopping_list = ShoppingList(name="To be deleted", home_id=home_id)
    await repo.save(shopping_list)
    
    # Ensure exists
    assert await repo.get_by_id(shopping_list.id) is not None
    
    # Delete
    await repo.delete(shopping_list.id)
    
    # Verify gone
    assert await repo.get_by_id(shopping_list.id) is None

@pytest.mark.asyncio
async def test_db_empty_list_persistence():
    """
    Scenario: Saving a list with no items.
    """
    repo = testing_container.shopping_list_repo
    home_id = await create_home_context()
    
    empty_list = ShoppingList(name="Empty", home_id=home_id)
    await repo.save(empty_list)
    
    fetched = await repo.get_by_id(empty_list.id)
    assert fetched.items == []