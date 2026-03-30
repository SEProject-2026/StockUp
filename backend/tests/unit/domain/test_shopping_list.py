from datetime import datetime
import pytest
from freezegun import freeze_time
from src.domain.enums import LocationType

# --- Basic Item Management ---

def test_add_item_new_success(empty_list):
    """Verify adding a new item to the list."""
    empty_list.add_item(item_name="Milk", quantity=2)
    
    assert len(empty_list.items) == 1
    assert empty_list.items[0].item_name == "Milk"
    assert empty_list.items[0].quantity == 2

def test_add_item_existing_merges_quantity(empty_list):
    """Verify that adding an existing item name updates the quantity instead of duplicating."""
    empty_list.add_item(item_name="Bread", quantity=1)
    empty_list.add_item(item_name="Bread", quantity=2)
    
    assert len(empty_list.items) == 1
    assert empty_list.items[0].quantity == 3

def test_remove_item_success(empty_list):
    empty_list.add_item(item_name="Eggs", quantity=12)
    empty_list.remove_item("Eggs")
    
    assert len(empty_list.items) == 0

def test_update_quantity_success(empty_list):
    empty_list.add_item(item_name="Apples", quantity=5)
    empty_list.update_quantity("Apples", 10)
    
    assert empty_list.items[0].quantity == 10

# --- Shopping Mode Logic ---

def test_shopping_mode_toggle(empty_list):
    assert empty_list.is_active_shopping_mode is False
    
    empty_list.enter_shopping_mode()
    assert empty_list.is_active_shopping_mode is True
    
    empty_list.exit_shopping_mode()
    assert empty_list.is_active_shopping_mode is False

def test_check_item_as_bought_toggle(empty_list):
    """Verify that checking an item toggles its is_bought status."""
    empty_list.add_item(item_name="Cheese", quantity=1)
    
    # Check
    empty_list.check_item_as_bought("Cheese")
    assert empty_list.items[0].is_bought is True

def test_exit_shopping_mode_with_clear(empty_list):
    """Verify that exiting with clear=True removes only bought items."""
    empty_list.add_item(item_name="Bought Item", quantity=1)
    empty_list.add_item(item_name="Leftover Item", quantity=1)
    
    empty_list.check_item_as_bought("Bought Item")
    
    # Exit and clear
    empty_list.exit_shopping_mode(clear=True)
    
    assert len(empty_list.items) == 1
    assert empty_list.items[0].item_name == "Leftover Item"

# --- Timestamp Logic ---

@freeze_time("2026-03-25 12:00:00")
def test_timestamp_refreshes_on_changes(empty_list):
    """Verify that updated_at changes whenever the list is modified."""
    
    # Now this will work because we imported the datetime class
    empty_list.updated_at = datetime.now() 
    initial_time = empty_list.updated_at

    with freeze_time("2026-03-25 12:05:00"):
        empty_list.add_item("Coffee", 1)
        # Ensure your add_item method in shopping_list.py calls self._refresh_timestamp()
        assert empty_list.updated_at > initial_time
        
    current_time = empty_list.updated_at
    with freeze_time("2026-03-25 12:10:00"):
        empty_list.check_item_as_bought("Coffee")
        assert empty_list.updated_at > current_time