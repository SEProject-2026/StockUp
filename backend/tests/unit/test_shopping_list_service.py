import pytest
from uuid import UUID, uuid4
from src.domain.enums import LocationType
from tests.container import testing_container
from src.domain.shopping_list.shopping_list import ShoppingList

# --- Setup Helpers ---

def setup_function():
    """
    Reset testing container state before every test to ensure isolation.
    """
    testing_container.activate_memory_mode()
    testing_container.reset_state()

async def setup_shopping_env():
    """
    Helper to set up a user and a home for shopping list tests.
    """
    user = await testing_container.user_service.register(
        "shop_test@test.com", "Secret123!", "Secret123!", "Shopper"
    )
    home = await testing_container.management_service.create_home(user.id, "Test Home")
    return user.id, home.get_id()

# --- Shopping List Service Tests ---

@pytest.mark.asyncio
async def test_create_shopping_list_success():
    """
    Scenario: User creates a new shopping list for their home.
    """
    _, home_id = await setup_shopping_env()
    list_name = "Weekly Groceries"

    # Act
    new_list = await testing_container.shopping_list_service.create_shopping_list(
        home_id=home_id, name=list_name
    )

    # Assert
    assert isinstance(new_list, ShoppingList)
    assert new_list.name == list_name
    assert new_list.home_id == home_id
    
    # Verify persistence in Repository
    retrieved = await testing_container.shopping_list_repo.get_by_id(new_list.id)
    assert retrieved is not None
    assert retrieved.name == list_name

@pytest.mark.asyncio
async def test_add_item_to_list_success():
    """
    Scenario: Adding an item to an existing list.
    """
    _, home_id = await setup_shopping_env()
    shopping_list = await testing_container.shopping_list_service.create_shopping_list(home_id, "Home List")

    # Act
    updated_list = await testing_container.shopping_list_service.add_item_to_list(
        id=shopping_list.id,
        item_name="Milk",
        quantity=2,
        location=LocationType.FRIDGE
    )

    # Assert
    assert len(updated_list.items) == 1
    assert updated_list.items[0].item_name == "Milk"
    assert updated_list.items[0].quantity == 2
    assert updated_list.items[0].location == LocationType.FRIDGE

@pytest.mark.asyncio
async def test_check_item_as_bought():
    """
    Scenario: Marking an item as bought in the list.
    """
    _, home_id = await setup_shopping_env()
    shopping_list = await testing_container.shopping_list_service.create_shopping_list(home_id, "List")
    await testing_container.shopping_list_service.add_item_to_list(shopping_list.id, "Eggs", 12)

    # Act
    updated_list = await testing_container.shopping_list_service.check_item_as_bought(
        id=shopping_list.id,
        item_name="Eggs"
    )

    # Assert
    assert updated_list.items[0].is_bought is True

@pytest.mark.asyncio
async def test_exit_shopping_mode_clears_bought_items():
    """
    Scenario: Exit shopping mode with clear=True should remove only bought items.
    """
    _, home_id = await setup_shopping_env()
    shopping_list = await testing_container.shopping_list_service.create_shopping_list(home_id, "Market List")
    
    # Setup: 1 bought item, 1 unbought item
    await testing_container.shopping_list_service.add_item_to_list(shopping_list.id, "Milk", 1)
    await testing_container.shopping_list_service.add_item_to_list(shopping_list.id, "Bread", 1)
    await testing_container.shopping_list_service.check_item_as_bought(shopping_list.id, "Milk")

    # Act
    final_list = await testing_container.shopping_list_service.exit_shopping_mode(
        id=shopping_list.id,
        clear=True
    )

    # Assert
    assert len(final_list.items) == 1
    assert final_list.items[0].item_name == "Bread" # Unbought remains
    assert final_list.is_active_shopping_mode is False

@pytest.mark.asyncio
async def test_get_all_shopping_lists_by_home():
    """
    Scenario: Home has multiple lists, retrieve all of them.
    """
    _, home_id = await setup_shopping_env()
    await testing_container.shopping_list_service.create_shopping_list(home_id, "List A")
    await testing_container.shopping_list_service.create_shopping_list(home_id, "List B")

    # Act
    all_lists = await testing_container.shopping_list_service.get_all_shopping_lists_by_home(home_id)

    # Assert
    assert len(all_lists) == 2
    names = [lst.name for lst in all_lists]
    assert "List A" in names
    assert "List B" in names

@pytest.mark.asyncio
async def test_delete_shopping_list():
    """
    Scenario: Delete a shopping list by ID.
    """
    _, home_id = await setup_shopping_env()
    shopping_list = await testing_container.shopping_list_service.create_shopping_list(home_id, "To Delete")

    # Act
    await testing_container.shopping_list_service.delete_shopping_list(shopping_list.id)

    # Assert
    all_lists = await testing_container.shopping_list_service.get_all_shopping_lists_by_home(home_id)
    assert len(all_lists) == 0

@pytest.mark.asyncio
async def test_service_raises_value_error_if_list_missing():
    """
    Scenario: Operating on a non-existent list ID should raise ValueError.
    """
    _, home_id = await setup_shopping_env()
    fake_id = uuid4()

    with pytest.raises(ValueError, match="Shopping list not found"):
        await testing_container.shopping_list_service.add_item_to_list(fake_id, "Milk", 1)