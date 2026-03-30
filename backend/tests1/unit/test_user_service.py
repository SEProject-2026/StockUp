import pytest
from uuid import UUID
from src.services.user_service import UserService
from src.authentication.auth_provider import IAuthProvider
from src.infrastructure.repositories.in_memory_user_repository import InMemoryUserRepository

# --- 1. Mocks ---

class MockAuthProvider(IAuthProvider):
    """
    Mock implementation of AuthProvider to avoid dependency on JWT library during unit tests.
    """
    def create_token(self, user_id: UUID) -> str:
        return f"fake_token_for_{user_id}"

    def verify_token(self, token: str) -> UUID:
        return UUID(token.split("_")[-1]) if "_" in token else None

# --- 2. Fixtures ---

@pytest.fixture
def user_service():
    """
    Pytest fixture to setup the service with in-memory dependencies before each test.
    """
    repo = InMemoryUserRepository()
    auth = MockAuthProvider()
    service = UserService(repo, auth)
    return service

# --- 3. Tests ---

@pytest.mark.asyncio
async def test_register_success(user_service):
    """
    Test that a valid registration creates a user and stores it in the repository.
    """
    # Act
    fake_uid = "550e8400-e29b-41d4-a716-446655440000"
    user = await user_service.register("dave@test.com",fake_uid, "Dave")
    
    # Assert
    assert user.email == "dave@test.com"
    assert user.name == "Dave"
    assert user.id == fake_uid
    
    # Assert persistence (check if saved in repo)
    saved_user = await user_service.user_repo.get_by_email("dave@test.com")
    assert saved_user is not None
    assert saved_user.id == fake_uid
@pytest.mark.asyncio
async def test_register_duplicate_email(user_service):
    """
    Test that registering with an existing email raises a ValueError.
    """
    # Arrange
    fake_uid1 = "550e8400-e29b-41d4-a716-446655440001"
    await user_service.register("dave@test.com", fake_uid1, "Dave")
    
    # Act & Assert
    with pytest.raises(ValueError) as excinfo:
        fake_uid2 = "550e8400-e29b-41d4-a716-446655440002"
        await user_service.register("dave@test.com", fake_uid2, "Dave 2")
    
    assert "already exists" in str(excinfo.value)

@pytest.mark.asyncio
async def test_update_name_logic(user_service):
    """
    Test the flow of updating a user profile name.
    """
    # Arrange
    fake_uid = "550e8400-e29b-41d4-a716-446655440000"
    user = await user_service.register("update@test.com", fake_uid, "Old Name")
    
    # Act
    updated_user = await user_service.update_name(user.id, "New Name")
    
    # Assert
    assert updated_user.name == "New Name"
    db_user = await user_service.user_repo.get_by_id(user.id)
    assert db_user.name == "New Name"
