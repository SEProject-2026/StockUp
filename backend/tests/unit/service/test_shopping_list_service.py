import pytest
import uuid
from unittest.mock import MagicMock

class TestShoppingListService:

    # ==========================================
    # 1. Lifecycle & CRUD (Create, Get, Delete)
    # ==========================================

    @pytest.mark.asyncio
    async def test_create_shopping_list_success(self, shopping_list_service, mock_shopping_repo):
        """Happy Path: Create a new shopping list for a home."""
        home_id = uuid.uuid4()
        list_name = "Party Prep"

        new_list = await shopping_list_service.create_shopping_list(home_id, list_name)

        assert new_list.name == list_name
        assert new_list.home_id == home_id
        mock_shopping_repo.save.assert_called_once_with(new_list)

    @pytest.mark.asyncio
    async def test_get_shopping_list_not_found_raises_error(self, shopping_list_service, mock_shopping_repo):
        """Sad Path: Retrieve a list ID that does not exist."""
        fake_id = uuid.uuid4()
        mock_shopping_repo.get_by_id.return_value = None

        with pytest.raises(ValueError, match=f"Shopping list not found: {fake_id}"):
            await shopping_list_service.get_shopping_list(fake_id)

    @pytest.mark.asyncio
    async def test_delete_shopping_list_success(self, shopping_list_service, mock_shopping_repo):
        """Happy Path: Delete a shopping list by ID."""
        list_id = uuid.uuid4()
        await shopping_list_service.delete_shopping_list(list_id)
        mock_shopping_repo.delete.assert_called_once_with(list_id)

    @pytest.mark.asyncio
    async def test_get_shopping_list_success(self, shopping_list_service, mock_shopping_repo, any_shopping_list):
        """Happy Path: Successfully retrieve an existing shopping list."""
        mock_shopping_repo.get_by_id.return_value = any_shopping_list

        result = await shopping_list_service.get_shopping_list(any_shopping_list.id)

        assert result.id == any_shopping_list.id
        assert result.name == any_shopping_list.name
        mock_shopping_repo.get_by_id.assert_called_once_with(any_shopping_list.id)

    # ==========================================
    # 2. Item Management (Add, Remove, Update)
    # ==========================================

    @pytest.mark.asyncio
    async def test_add_item_to_list_success(self, shopping_list_service, mock_shopping_repo, any_shopping_list):
        """Happy Path: Adding an item to an existing list."""
        mock_shopping_repo.get_by_id.return_value = any_shopping_list
        
        updated_list = await shopping_list_service.add_item_to_list(
            any_shopping_list.id, "Apples", 5
        )

        assert any(item.item_name == "Apples" for item in updated_list.items)
        mock_shopping_repo.save.assert_called_once_with(any_shopping_list)

    @pytest.mark.asyncio
    async def test_update_item_quantity_success(self, shopping_list_service, mock_shopping_repo, any_shopping_list):
        """Happy Path: Changing quantity of an existing item."""
        any_shopping_list.add_item("Eggs", 6)
        mock_shopping_repo.get_by_id.return_value = any_shopping_list

        updated_list = await shopping_list_service.update_item_quantity(
            any_shopping_list.id, "Eggs", 12
        )

        item = next(i for i in updated_list.items if i.item_name == "Eggs")
        assert item.quantity == 12
        mock_shopping_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_item_from_list_success(self, shopping_list_service, mock_shopping_repo, any_shopping_list):
        """Happy Path: Removing an item and persisting changes."""
        any_shopping_list.add_item("Milk", 1)
        mock_shopping_repo.get_by_id.return_value = any_shopping_list

        updated_list = await shopping_list_service.remove_item_from_list(any_shopping_list.id, "Milk")

        assert not any(item.item_name == "Milk" for item in updated_list.items)
        mock_shopping_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_non_existent_item_raises_error(self, shopping_list_service, mock_shopping_repo, any_shopping_list):
        """Sad Path: User tries to remove an item that isn't on the list."""
        mock_shopping_repo.get_by_id.return_value = any_shopping_list
        with pytest.raises(ValueError, match="not found"):
            await shopping_list_service.remove_item_from_list(any_shopping_list.id, "NonExistentItem")

    # ==========================================
    # 3. Shopping Mode Logic
    # ==========================================

    @pytest.mark.asyncio
    async def test_enter_shopping_mode_success(self, shopping_list_service, mock_shopping_repo, any_shopping_list):
        """Happy Path: Activate shopping mode."""
        mock_shopping_repo.get_by_id.return_value = any_shopping_list

        updated_list = await shopping_list_service.enter_shopping_mode(any_shopping_list.id)

        assert updated_list.is_active_shopping_mode is True
        mock_shopping_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_item_as_bought_success(self, shopping_list_service, mock_shopping_repo, any_shopping_list):
        """Happy Path: Marking an item as bought."""
        any_shopping_list.add_item("Milk", 2)
        mock_shopping_repo.get_by_id.return_value = any_shopping_list

        updated_list = await shopping_list_service.check_item_as_bought(any_shopping_list.id, "Milk")

        item = next(i for i in updated_list.items if i.item_name == "Milk")
        assert item.is_bought is True
        mock_shopping_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_exit_shopping_mode_with_clear(self, shopping_list_service, mock_shopping_repo, any_shopping_list):
        """Happy Path: Exiting and clearing bought items."""
        any_shopping_list.add_item("Bought", 1)
        any_shopping_list.add_item("Remaining", 1)
        any_shopping_list.check_item_as_bought("Bought")
        mock_shopping_repo.get_by_id.return_value = any_shopping_list

        updated_list = await shopping_list_service.exit_shopping_mode(any_shopping_list.id, clear=True)

        assert len(updated_list.items) == 1
        assert updated_list.items[0].item_name == "Remaining"
        assert updated_list.is_active_shopping_mode is False

    @pytest.mark.asyncio
    async def test_exit_shopping_mode_without_clear(self, shopping_list_service, mock_shopping_repo, any_shopping_list):
        """Happy Path: Exiting without clearing items."""
        any_shopping_list.add_item("Bought", 1)
        any_shopping_list.check_item_as_bought("Bought")
        mock_shopping_repo.get_by_id.return_value = any_shopping_list

        updated_list = await shopping_list_service.exit_shopping_mode(any_shopping_list.id, clear=False)

        assert len(updated_list.items) == 1
        assert updated_list.items[0].is_bought is True
        assert updated_list.is_active_shopping_mode is False

    # ==========================================
    # 4. Home Level Operations
    # ==========================================

    @pytest.mark.asyncio
    async def test_get_all_shopping_lists_by_home_success(self, shopping_list_service, mock_shopping_repo):
        """Happy Path: Retrieve all lists for a specific home."""
        home_id = uuid.uuid4()
        mock_lists = [uuid.uuid4(), uuid.uuid4()]
        mock_shopping_repo.get_all_by_home.return_value = mock_lists

        results = await shopping_list_service.get_all_shopping_lists_by_home(home_id)

        assert len(results) == 2
        assert results == mock_lists
        mock_shopping_repo.get_all_by_home.assert_called_once_with(home_id)

    # ==========================================
    # 5. Sad Paths (Service Level Validations)
    # ==========================================

    @pytest.mark.asyncio
    async def test_add_item_to_non_existent_list_fails(self, shopping_list_service, mock_shopping_repo):
        """Sad Path: Trying to add an item to a list that doesn't exist."""
        fake_id = uuid.uuid4()
        mock_shopping_repo.get_by_id.return_value = None

        with pytest.raises(ValueError, match=f"Shopping list not found: {fake_id}"):
            await shopping_list_service.add_item_to_list(fake_id, "Milk", 2)

    @pytest.mark.asyncio
    async def test_enter_shopping_mode_non_existent_list_fails(self, shopping_list_service, mock_shopping_repo):
        """Sad Path: Trying to enter shopping mode for a list that doesn't exist."""
        fake_id = uuid.uuid4()
        mock_shopping_repo.get_by_id.return_value = None

        with pytest.raises(ValueError, match=f"Shopping list not found: {fake_id}"):
            await shopping_list_service.enter_shopping_mode(fake_id)