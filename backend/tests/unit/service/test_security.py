import pytest
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.security import validate_home_membership, require_house_access

@pytest.fixture(autouse=True)
def unmock_security():
    """
    Ensure we are testing the REAL decorator and validation logic,
    not the global mock from conftest.py.
    """
    # We patch it with its own original implementation
    with patch("src.services.security.validate_home_membership", side_effect=validate_home_membership):
        yield

@pytest.mark.asyncio
async def test_validate_home_membership_success():
    """Verifies that valid membership returns the home object."""
    mock_repo = AsyncMock()
    user_id = uuid4()
    home_id = uuid4()
    
    mock_home = MagicMock()
    mock_home.is_member.return_value = True
    mock_repo.get_by_id.return_value = mock_home
    
    result = await validate_home_membership(mock_repo, user_id, home_id)
    
    assert result == mock_home
    mock_repo.get_by_id.assert_called_once_with(home_id)
    mock_home.is_member.assert_called_once_with(user_id)

@pytest.mark.asyncio
async def test_validate_home_membership_not_member_raises_error():
    """Verifies that non-membership raises ValueError."""
    mock_repo = AsyncMock()
    user_id = uuid4()
    home_id = uuid4()
    
    mock_home = MagicMock()
    mock_home.is_member.return_value = False
    mock_repo.get_by_id.return_value = mock_home
    
    with pytest.raises(ValueError, match="User is not a member"):
        await validate_home_membership(mock_repo, user_id, home_id)

@pytest.mark.asyncio
async def test_validate_home_membership_home_not_found():
    """Verifies that missing home raises ValueError."""
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = None
    
    with pytest.raises(ValueError, match="Home retrieval failed"):
        await validate_home_membership(mock_repo, uuid4(), uuid4())

# --- Decorator Tests ---

class MockService:
    def __init__(self, repo):
        self._home_repository = repo
    
    @require_house_access
    async def some_method(self, user_id, home_id, other_arg):
        return f"success-{other_arg}"

    @require_house_access
    async def method_with_injection(self, user_id, home_id, home=None):
        return home

class MockShoppingService:
    def __init__(self, shopping_repo, home_repo):
        self.shopping_repo = shopping_repo
        self._home_repository = home_repo
    
    @require_house_access
    async def list_method(self, user_id, id):
        return "list-success"

@pytest.mark.asyncio
async def test_require_house_access_decorator_direct_args():
    """Verifies decorator works with direct user_id and home_id arguments."""
    mock_repo = AsyncMock()
    mock_home = MagicMock()
    mock_home.is_member.return_value = True
    mock_repo.get_by_id.return_value = mock_home
    
    service = MockService(mock_repo)
    user_id = uuid4()
    home_id = uuid4()
    
    result = await service.some_method(user_id, home_id, "test")
    
    assert result == "success-test"

@pytest.mark.asyncio
async def test_require_house_access_decorator_injection():
    """Verifies decorator injects the 'home' object when requested."""
    mock_repo = AsyncMock()
    mock_home = MagicMock()
    mock_home.is_member.return_value = True
    mock_repo.get_by_id.return_value = mock_home
    
    service = MockService(mock_repo)
    
    # We call the method without passing 'home'
    result = await service.method_with_injection(uuid4(), uuid4())
    
    assert result == mock_home

@pytest.mark.asyncio
async def test_require_house_access_decorator_list_id_resolution():
    """Verifies decorator resolves home_id from list_id for ShoppingListService."""
    mock_home_repo = AsyncMock()
    mock_shopping_repo = AsyncMock()
    
    mock_home = MagicMock()
    mock_home.is_member.return_value = True
    mock_home_repo.get_by_id.return_value = mock_home
    
    mock_list = MagicMock()
    mock_list.home_id = uuid4()
    mock_shopping_repo.get_by_id.return_value = mock_list
    
    service = MockShoppingService(mock_shopping_repo, mock_home_repo)
    
    # We call with user_id and id (list_id), but NO home_id
    result = await service.list_method(uuid4(), uuid4())
    
    assert result == "list-success"
    mock_shopping_repo.get_by_id.assert_called_once()
    mock_home_repo.get_by_id.assert_called_once_with(mock_list.home_id)
