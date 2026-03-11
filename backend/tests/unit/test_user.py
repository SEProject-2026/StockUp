import pytest
from uuid import UUID
from src.domain.user.user import User

def test_user_initialization():
    """
    Test that a new User entity is created with correct default values.
    """
    # Act
    user = User(email="test@test.com", name="Test User", hashed_password="hashed_secret")
    
    # Assert
    assert user.email == "test@test.com"
    assert user.name == "Test User"
    assert user.hashed_password == "hashed_secret"
    # Verify that ID is generated automatically
    assert isinstance(user.id, UUID)

def test_update_name_success():
    """
    Test that update_name correctly changes the user's name.
    """
    # Arrange
    user = User(email="test@test.com", name="Old Name", hashed_password="hash")
    
    # Act
    user.update_name("New Name")
    
    # Assert
    assert user.name == "New Name"

def test_change_password_entity():
    """
    Test that the password field is updated correctly in the entity.
    """
    # Arrange
    user = User(email="test@test.com", name="User", hashed_password="old_hash")
    
    # Act
    user.change_password("new_hash")
    
    # Assert
    assert user.hashed_password == "new_hash"