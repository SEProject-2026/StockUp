import pytest
from uuid import UUID
from src.domain.user.user import User

def test_user_initialization():
    """
    Test that a new User entity is created with correct default values.
    """
    # Act
    fake_uid = "550e8400-e29b-41d4-a716-446655440000"
    user = User(id=fake_uid, email="test@test.com", name="Test User")

    # Assert
    assert user.email == "test@test.com"
    assert user.name == "Test User"
    assert user.id == fake_uid

def test_update_name_success():
    """
    Test that update_name correctly changes the user's name.
    """
    # Arrange
    fake_uid = "550e8400-e29b-41d4-a716-446655440000"
    user = User(id=fake_uid, email="test@test.com", name="Old Name")
    
    # Act
    user.update_name("New Name")
    
    # Assert
    assert user.name == "New Name"