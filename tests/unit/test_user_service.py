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
    user = await user_service.register("dave@test.com", "password123", "Dave")
    
    # Assert
    assert user.email == "dave@test.com"
    assert user.name == "Dave"
    assert isinstance(user.id, UUID)
    
    # Assert persistence (check if saved in repo)
    saved_user = await user_service.user_repo.get_by_email("dave@test.com")
    assert saved_user is not None
    assert saved_user.hashed_password != "password123" 

@pytest.mark.asyncio
async def test_register_duplicate_email(user_service):
    """
    Test that registering with an existing email raises a ValueError.
    """
    # Arrange
    await user_service.register("dave@test.com", "12345678", "Dave")
    
    # Act & Assert
    with pytest.raises(ValueError) as excinfo:
        await user_service.register("dave@test.com", "87654321", "Dave 2")
    
    assert "already exists" in str(excinfo.value)

@pytest.mark.asyncio
async def test_login_success(user_service):
    """
    Test that valid credentials return a User object and a token.
    """
    # Arrange
    await user_service.register("login@test.com", "secret123", "Login User")
    
    # Act
    user, token = await user_service.login("login@test.com", "secret123")
    
    # Assert
    assert user.email == "login@test.com"
    assert "fake_token" in token 

@pytest.mark.asyncio
async def test_login_wrong_password(user_service):
    """
    Test that login fails when the password is incorrect.
    """
    # Arrange
    await user_service.register("wrong@test.com", "secret123", "User")
    
    # Act & Assert
    with pytest.raises(ValueError) as excinfo:
        await user_service.login("wrong@test.com", "WRONG_PASSWORD")
    
    assert "Invalid email or password" in str(excinfo.value)

@pytest.mark.asyncio
async def test_update_name_logic(user_service):
    """
    Test the flow of updating a user profile name.
    """
    # Arrange
    user = await user_service.register("update@test.com", "12345678", "Old Name")
    
    # Act
    updated_user = await user_service.update_name(user.id, "New Name")
    
    # Assert
    assert updated_user.name == "New Name"
    db_user = await user_service.user_repo.get_by_id(user.id)
    assert db_user.name == "New Name"

@pytest.mark.asyncio
async def test_change_password_success(user_service):
    """
    Test the successful flow of changing a password.
    """
    # Arrange
    email = "pass_change@test.com"
    old_pass = "OldPass123"
    new_pass = "NewPass456"
    
    user = await user_service.register(email, old_pass, "User")

    # Act
    await user_service.change_password(user.id, old_pass, new_pass)

    # Verification: Login with OLD password should fail
    with pytest.raises(ValueError):
        await user_service.login(email, old_pass)

    user, token = await user_service.login(email, new_pass)
    assert token is not None