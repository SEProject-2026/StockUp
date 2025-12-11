import pytest
from uuid import UUID

from services.user_service import UserService
from authentication.auth_provider import IAuthProvider
from infrastructure.repositories.in_memory_user_repository import InMemoryUserRepository

# --- 1. Mocks ---

class MockAuthProvider(IAuthProvider):
    """
    Mock implementation of AuthProvider to avoid dependency on JWT library during unit tests.
    """
    def create_token(self, user_id: UUID) -> str:
        return f"fake_token_for_{user_id}"

    def verify_token(self, token: str) -> UUID:
        # In tests, we assume valid format or handle specifically if needed
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
    result = await user_service.register("dave@test.com", "password123", "Dave")
    
    # Assert response structure
    assert result["status"] == "success"
    assert result["data"]["email"] == "dave@test.com"
    assert "id" in result["data"]
    
    # Assert persistence (check if saved in repo)
    saved_user = await user_service.user_repo.get_by_email("dave@test.com")
    assert saved_user is not None
    assert saved_user.name == "Dave"
    
    # Security check: Password must not be stored in plain text
    assert saved_user.hashed_password != "password123" 

@pytest.mark.asyncio
async def test_register_duplicate_email(user_service):
    """
    Test that registering with an existing email raises a ValueError.
    """
    # Arrange: Register the first user
    await user_service.register("dave@test.com", "12345678", "Dave")
    
    # Act & Assert: Try to register again with the same email
    with pytest.raises(ValueError) as excinfo:
        await user_service.register("dave@test.com", "87654321", "Dave 2")
    
    assert "already exists" in str(excinfo.value)

@pytest.mark.asyncio
async def test_login_success(user_service):
    """
    Test that valid credentials return a success status and an access token.
    """
    # Arrange
    await user_service.register("login@test.com", "secret123", "Login User")
    
    # Act
    response = await user_service.login("login@test.com", "secret123")
    
    # Assert
    assert response["status"] == "success"
    assert "access_token" in response
    # Verify we got the mock token
    assert "fake_token" in response["access_token"] 

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
    reg_data = await user_service.register("update@test.com", "12345678", "Old Name")
    user_id = reg_data["data"]["id"]
    
    # Act
    await user_service.update_name(user_id, "New Name")
    
    # Assert
    updated_user = await user_service.user_repo.get_by_id(user_id)
    assert updated_user.name == "New Name"

@pytest.mark.asyncio
async def test_change_password_success(user_service):
    """
    Test the successful flow of changing a password.
    Verifies that the new password can be used for login.
    """
    # Arrange: Create a user
    email = "pass_change@test.com"
    old_pass = "OldPass123"
    new_pass = "NewPass456"
    
    reg_data = await user_service.register(email, old_pass, "User")
    user_id = reg_data["data"]["id"]

    # Act: Change the password
    result = await user_service.change_password(user_id, old_pass, new_pass)

    # Assert: Operation successful (Checking dictionary status instead of boolean)
    assert result["status"] == "success" 
    assert result["message"] == "Password changed successfully"

    # Verification: Try to login with the OLD password (should fail)
    with pytest.raises(ValueError):
        await user_service.login(email, old_pass)

    # Verification: Try to login with the NEW password (should succeed)
    login_response = await user_service.login(email, new_pass)
    assert login_response["status"] == "success"

@pytest.mark.asyncio
async def test_change_password_invalid_new(user_service):
    """
    Test that the new password must meet complexity requirements (e.g. length).
    """
    # Arrange
    reg_data = await user_service.register("short_new@test.com", "ValidPass1", "User")
    user_id = reg_data["data"]["id"]

    # Act & Assert
    with pytest.raises(ValueError) as excinfo:
        # Trying to set a short password
        await user_service.change_password(user_id, "ValidPass1", "short")
    
    assert "New password is too short" in str(excinfo.value)