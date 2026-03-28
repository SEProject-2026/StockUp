import pytest
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from time import sleep
from src.domain.shopping_list.shopping_list import ShoppingList, ShoppingListItem

# --- Fixtures ---

@pytest.fixture
def empty_list():
    """Provides a fresh shopping list for each test."""
    return ShoppingList(
        name="Weekly Groceries",
        home_id=uuid4()
    )

@pytest.fixture
def populated_list(empty_list):
    """Provides a list with some items already added."""
    empty_list.add_item("Milk", 2, "FRIDGE")
    empty_list.add_item("Bread", 1, "PANTRY")
    return empty_list

# --- Tests ---

def test_add_new_item(empty_list):
    """Test adding a brand new item to the list with a standard location."""
    empty_list.add_item("Apples", 5, "PANTRY")
    
    assert len(empty_list.items) == 1
    assert empty_list.items[0].item_name == "Apples"
    assert empty_list.items[0].quantity == 5
    assert empty_list.items[0].location == "PANTRY"

def test_add_item_with_custom_location(empty_list):
    """Test adding an item with a completely custom string location."""
    empty_list.add_item("Sushi", 1, "Ma'afiya")
    
    assert len(empty_list.items) == 1
    assert empty_list.items[0].item_name == "Sushi"
    assert empty_list.items[0].location == "Ma'afiya"

def test_add_existing_item_updates_quantity(populated_list):
    """Test that adding an existing item increases its quantity instead of duplicating."""
    initial_len = len(populated_list.items)
    populated_list.add_item("Milk", 3)
    
    assert len(populated_list.items) == initial_len
    # Find milk and check quantity: 2 (initial) + 3 (new) = 5
    milk_item = next(i for i in populated_list.items if i.item_name == "Milk")
    assert milk_item.quantity == 5

def test_remove_item(populated_list):
    """Test removing an item from the list."""
    populated_list.remove_item("Milk")
    assert len(populated_list.items) == 1
    assert all(i.item_name != "Milk" for i in populated_list.items)

def test_update_quantity(populated_list):
    """Test explicitly updating an item's quantity."""
    populated_list.update_quantity("Bread", 10)
    bread_item = next(i for i in populated_list.items if i.item_name == "Bread")
    assert bread_item.quantity == 10

def test_shopping_mode_toggle(empty_list):
    """Test entering and exiting shopping mode."""
    assert not empty_list.is_active_shopping_mode
    empty_list.enter_shopping_mode()
    assert empty_list.is_active_shopping_mode
    empty_list.exit_shopping_mode(clear=False)
    assert not empty_list.is_active_shopping_mode

def test_check_item_as_bought(populated_list):
    """Test marking an item as bought."""
    populated_list.check_item_as_bought("Milk")
    milk_item = next(i for i in populated_list.items if i.item_name == "Milk")
    assert milk_item.is_bought is True

def test_exit_shopping_mode_with_clear(populated_list):
    """
    Test that exiting with clear=True removes only bought items 
    and keeps unbought ones.
    """
    populated_list.check_item_as_bought("Milk") # Bought
    # Bread is NOT bought
    
    populated_list.exit_shopping_mode(clear=True)
    
    assert len(populated_list.items) == 1
    assert populated_list.items[0].item_name == "Bread"
    assert populated_list.is_active_shopping_mode is False

def test_timestamp_refreshes_on_mutation(empty_list):
    """
    Test that updated_at timestamp changes when the list is modified.
    Using a small sleep to ensure clock tick.
    """
    initial_timestamp = empty_list.updated_at
    sleep(0.01) # Force time difference
    
    empty_list.add_item("Eggs", 12)
    
    assert empty_list.updated_at > initial_timestamp

def test_uuid_generation():
    """Test that every ShoppingList gets a unique UUID by default."""
    list_a = ShoppingList(name="A", home_id=uuid4())
    list_b = ShoppingList(name="B", home_id=uuid4())
    assert list_a.id != list_b.id
    assert isinstance(list_a.id, UUID)