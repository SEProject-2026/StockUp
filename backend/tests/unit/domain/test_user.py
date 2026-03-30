import uuid
import pytest
from src.domain.user.user import User

def test_user_initialization(any_user):
    """
    Verify that a user is created with correct attributes.
    'any_user' is injected from global conftest.py
    """
    assert isinstance(any_user.id, uuid.UUID)
    assert "@stockup.com" in any_user.email
    assert any_user.name == "Test User"

def test_user_creation_with_empty_name_fails():
    """
    This test still uses the factory directly because it tests 
    the failure of the creation process itself.
    """
    with pytest.raises(ValueError, match="User name cannot be empty"):
        User(id=uuid.uuid4(), email="test@test.com", name="", push_token="123")

def test_user_update_name(any_user):
    """Verify the domain logic for updating a user's name."""
    any_user.update_name("New Name")
    assert any_user.name == "New Name"

def test_user_update_name_to_empty_fails(any_user):
    """Verify validation when updating to an empty name."""
    with pytest.raises(ValueError, match="User name cannot be empty"):
        any_user.update_name("   ")

def test_user_update_push_token(any_user):
    """Verify push token update."""
    new_token = "token_123"
    any_user.update_push_token(new_token)
    assert any_user.push_token == new_token