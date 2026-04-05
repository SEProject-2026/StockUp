import pytest
from datetime import datetime
from freezegun import freeze_time
from src.domain.enums import LocationType

class TestShoppingListDomain:

    # ==========================================
    # 1. Item Management (Add, Remove, Update)
    # ==========================================

    def test_add_item_new_success(self, any_shopping_list):
        """Happy Path: Adding a brand new item."""
        any_shopping_list.add_item(item_name="Milk", quantity=2)
        
        assert len(any_shopping_list.items) == 1
        assert any_shopping_list.items[0].item_name == "Milk"
        assert any_shopping_list.items[0].quantity == 2

    def test_add_item_existing_merges_quantity(self, any_shopping_list):
        """Happy Path: Adding an existing item name merges quantities."""
        any_shopping_list.add_item(item_name="Bread", quantity=1)
        any_shopping_list.add_item(item_name="Bread", quantity=2)
        
        assert len(any_shopping_list.items) == 1
        assert any_shopping_list.items[0].quantity == 3

    def test_update_quantity_success(self, any_shopping_list):
        """Happy Path: Updating quantity for an existing item."""
        any_shopping_list.add_item(item_name="Apples", quantity=5)
        any_shopping_list.update_quantity("Apples", 10)
        
        assert any_shopping_list.items[0].quantity == 10

    def test_remove_item_success(self, any_shopping_list):
        """Happy Path: Removing an item by name."""
        any_shopping_list.add_item(item_name="Eggs", quantity=12)
        any_shopping_list.remove_item("Eggs")
        
        assert len(any_shopping_list.items) == 0

    # ==========================================
    # 2. Shopping Mode & Bought Status
    # ==========================================

    def test_shopping_mode_toggle(self, any_shopping_list):
        """Happy Path: Toggling shopping mode status."""
        assert any_shopping_list.is_active_shopping_mode is False
        
        any_shopping_list.enter_shopping_mode()
        assert any_shopping_list.is_active_shopping_mode is True
        
        any_shopping_list.exit_shopping_mode()
        assert any_shopping_list.is_active_shopping_mode is False

    def test_check_item_as_bought_toggle(self, any_shopping_list):
        """Happy Path: Marking an item as bought."""
        any_shopping_list.add_item(item_name="Cheese", quantity=1)
        
        any_shopping_list.check_item_as_bought("Cheese")
        assert any_shopping_list.items[0].is_bought is True

    def test_exit_shopping_mode_with_clear(self, any_shopping_list):
        """Happy Path: Exiting shopping mode and clearing bought items."""
        any_shopping_list.add_item(item_name="Bought Item", quantity=1)
        any_shopping_list.add_item(item_name="Leftover Item", quantity=1)
        
        any_shopping_list.check_item_as_bought("Bought Item")
        
        # Exit and clear
        any_shopping_list.exit_shopping_mode(clear=True)
        
        assert len(any_shopping_list.items) == 1
        assert any_shopping_list.items[0].item_name == "Leftover Item"

    # ==========================================
    # 3. Timestamp Logic (Auto-refresh)
    # ==========================================

    @freeze_time("2026-03-25 12:00:00")
    def test_timestamp_refreshes_on_changes(self, any_shopping_list):
        """Internal Logic: Verify updated_at refreshes on every modification."""
        
        any_shopping_list.updated_at = datetime.now() 
        initial_time = any_shopping_list.updated_at

        # Modification 1: Add item
        with freeze_time("2026-03-25 12:05:00"):
            any_shopping_list.add_item("Coffee", 1)
            assert any_shopping_list.updated_at > initial_time
            
        current_time = any_shopping_list.updated_at
        
        # Modification 2: Check item
        with freeze_time("2026-03-25 12:10:00"):
            any_shopping_list.check_item_as_bought("Coffee")
            assert any_shopping_list.updated_at > current_time