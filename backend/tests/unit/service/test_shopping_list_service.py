import pytest
import uuid
from unittest.mock import MagicMock

class TestShoppingListService:

    # ==========================================
    # 1. Lifecycle & CRUD (Create, Get, Delete)
    # ==========================================

    @pytest.mark.asyncio
    async def test_create_shopping_list_success(self, shopping_list_service, mock_shopping_repo, active_service_context):
        """Happy Path: Create a new shopping list for a home."""
        home, user = active_service_context
        list_name = "Party Prep"

        new_list = await shopping_list_service.create_shopping_list(user.id, home._id, list_name)

        assert new_list.name == list_name
        assert new_list.home_id == home._id
        mock_shopping_repo.save.assert_called_once_with(new_list)

    @pytest.mark.asyncio
    async def test_get_shopping_list_success(self, shopping_list_service, mock_shopping_repo, active_service_context, any_shopping_list):
        """Happy Path: Retrieve a valid shopping list."""
        home, user = active_service_context
        mock_shopping_repo.get_by_id.return_value = any_shopping_list

        result = await shopping_list_service.get_shopping_list(user.id, any_shopping_list.id)

        assert result == any_shopping_list
        mock_shopping_repo.get_by_id.assert_called()

    @pytest.mark.asyncio
    async def test_get_shopping_list_not_found_raises_error(self, shopping_list_service, mock_shopping_repo, active_service_context):
        """Sad Path: Retrieve a list ID that does not exist."""
        home, user = active_service_context
        fake_id = uuid.uuid4()
        mock_shopping_repo.get_by_id.return_value = None

        with pytest.raises(ValueError, match=f"Shopping list not found: {fake_id}"):
            await shopping_list_service.get_shopping_list(user.id, fake_id)

    @pytest.mark.asyncio
    async def test_delete_shopping_list_success(self, shopping_list_service, mock_shopping_repo, active_service_context):
        """Happy Path: Delete a shopping list by ID."""
        home, user = active_service_context
        list_id = uuid.uuid4()
        
        # Mock list to resolve home_id during decorator execution
        mock_list = MagicMock()
        mock_list.home_id = home._id
        mock_shopping_repo.get_by_id.return_value = mock_list
        
        await shopping_list_service.delete_shopping_list(user.id, list_id)
        mock_shopping_repo.delete.assert_called_once_with(list_id)

    # ==========================================
    # 2. Item Management (Add, Remove, Update)
    # ==========================================

    @pytest.mark.asyncio
    async def test_add_item_to_list_success(self, shopping_list_service, mock_shopping_repo, any_shopping_list, active_service_context):
        """Happy Path: Adding an item to an existing list."""
        home, user = active_service_context
        mock_shopping_repo.get_by_id.return_value = any_shopping_list
        
        updated_list = await shopping_list_service.add_item_to_list(
            user.id, any_shopping_list.id, "Apples", 5
        )

        assert any(item.item_name == "Apples" for item in updated_list.items)
        mock_shopping_repo.save.assert_called_once_with(any_shopping_list)

    @pytest.mark.asyncio
    async def test_update_item_quantity_success(self, shopping_list_service, mock_shopping_repo, any_shopping_list, active_service_context):
        """Happy Path: Changing quantity of an existing item."""
        home, user = active_service_context
        any_shopping_list.add_item("Eggs", 6)
        mock_shopping_repo.get_by_id.return_value = any_shopping_list

        updated_list = await shopping_list_service.update_item_quantity(
            user.id, any_shopping_list.id, "Eggs", 12
        )

        item = next(i for i in updated_list.items if i.item_name == "Eggs")
        assert item.quantity == 12
        mock_shopping_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_item_from_list_success(self, shopping_list_service, mock_shopping_repo, any_shopping_list, active_service_context):
        """Happy Path: Removing an item and persisting changes."""
        home, user = active_service_context
        any_shopping_list.add_item("Milk", 1)
        mock_shopping_repo.get_by_id.return_value = any_shopping_list

        updated_list = await shopping_list_service.remove_item_from_list(user.id, any_shopping_list.id, "Milk")

        assert not any(item.item_name == "Milk" for item in updated_list.items)
        mock_shopping_repo.save.assert_called_once()

    # ==========================================
    # 3. Shopping Mode Logic
    # ==========================================

    @pytest.mark.asyncio
    async def test_enter_shopping_mode_success(self, shopping_list_service, mock_shopping_repo, any_shopping_list, active_service_context):
        """Happy Path: Activate shopping mode."""
        home, user = active_service_context
        mock_shopping_repo.get_by_id.return_value = any_shopping_list

        updated_list = await shopping_list_service.enter_shopping_mode(user.id, any_shopping_list.id)

        assert updated_list.is_active_shopping_mode is True
        mock_shopping_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_item_as_bought_success(self, shopping_list_service, mock_shopping_repo, any_shopping_list, active_service_context):
        """Happy Path: Marking an item as bought."""
        home, user = active_service_context
        any_shopping_list.add_item("Milk", 2)
        mock_shopping_repo.get_by_id.return_value = any_shopping_list

        updated_list = await shopping_list_service.check_item_as_bought(user.id, any_shopping_list.id, "Milk")

        item = next(i for i in updated_list.items if i.item_name == "Milk")
        assert item.is_bought is True
        mock_shopping_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_exit_shopping_mode_with_clear(self, shopping_list_service, mock_shopping_repo, any_shopping_list, active_service_context):
        """Happy Path: Exiting and clearing bought items."""
        home, user = active_service_context
        any_shopping_list.add_item("Bought", 1)
        any_shopping_list.add_item("Remaining", 1)
        any_shopping_list.check_item_as_bought("Bought")
        mock_shopping_repo.get_by_id.return_value = any_shopping_list

        updated_list = await shopping_list_service.exit_shopping_mode(user.id, any_shopping_list.id, clear=True)

        assert len(updated_list.items) == 1
        assert updated_list.items[0].item_name == "Remaining"
        assert updated_list.is_active_shopping_mode is False

    @pytest.mark.asyncio
    async def test_exit_shopping_mode_without_clear(self, shopping_list_service, mock_shopping_repo, any_shopping_list, active_service_context):
        """Happy Path: Exiting without clearing items."""
        home, user = active_service_context
        any_shopping_list.add_item("Bought", 1)
        any_shopping_list.check_item_as_bought("Bought")
        mock_shopping_repo.get_by_id.return_value = any_shopping_list

        updated_list = await shopping_list_service.exit_shopping_mode(user.id,    any_shopping_list.id, clear=False)

        assert len(updated_list.items) == 1
        assert updated_list.items[0].is_bought is True
        assert updated_list.is_active_shopping_mode is False

    # ==========================================
    # 4. Home Level Operations
    # ==========================================

    @pytest.mark.asyncio
    async def test_get_all_shopping_lists_by_home_success(self, shopping_list_service, mock_shopping_repo, active_service_context):
        """Happy Path: Retrieve all lists for a specific home."""
        home, user = active_service_context
        mock_lists = [uuid.uuid4(), uuid.uuid4()]
        mock_shopping_repo.get_all_by_home.return_value = mock_lists

        results = await shopping_list_service.get_all_shopping_lists_by_home(user.id, home._id)

        assert len(results) == 2
        assert results == mock_lists
        mock_shopping_repo.get_all_by_home.assert_called_once_with(home._id)

    # ==========================================
    # 5. Sad Paths (Service Level Validations)
    # ==========================================

    @pytest.mark.asyncio
    async def test_add_item_to_non_existent_list_fails(self, shopping_list_service, mock_shopping_repo, active_service_context):
        """Sad Path: Trying to add an item to a list that doesn't exist."""
        home, user = active_service_context
        fake_id = uuid.uuid4()
        mock_shopping_repo.get_by_id.return_value = None

        with pytest.raises(ValueError, match=f"Shopping list not found: {fake_id}"):
            await shopping_list_service.add_item_to_list(user.id, fake_id, "Milk", 2)

    @pytest.mark.asyncio
    async def test_enter_shopping_mode_non_existent_list_fails(self, shopping_list_service, mock_shopping_repo, active_service_context):
        """Sad Path: Trying to enter shopping mode for a list that doesn't exist."""
        home, user = active_service_context
        fake_id = uuid.uuid4()
        mock_shopping_repo.get_by_id.return_value = None

        with pytest.raises(ValueError, match=f"Shopping list not found: {fake_id}"):
            await shopping_list_service.enter_shopping_mode(user.id, fake_id)