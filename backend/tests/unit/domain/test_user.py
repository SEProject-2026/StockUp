import uuid
import pytest
from src.domain.user.user import User

class TestUserDomain:

    # ==========================================
    # 1. Initialization & Creation
    # ==========================================

    def test_user_initialization(self, any_user):
        """Happy Path: Verify that a user is created with correct attributes via fixture."""
        assert isinstance(any_user.id, uuid.UUID)
        assert "@test.com" in any_user.email 
        assert any_user.name == "Test User"

    def test_user_creation_with_empty_name_fails(self):
        """Sad Path: Verify validation prevents empty names during initialization."""
        with pytest.raises(ValueError, match="User name cannot be empty"):
            User(id=uuid.uuid4(), email="test@test.com", name="", push_token="123")
        
        with pytest.raises(ValueError, match="User name cannot be empty"):
            User(id=uuid.uuid4(), email="test@test.com", name="   ", push_token="123")
    
    def test_user_creation_with_invalid_email_fails(self):
        """Sad Path: Domain should reject empty or invalid emails."""
        with pytest.raises(ValueError, match="Invalid email address"):
            User(id=uuid.uuid4(), email="", name="David")
            
        with pytest.raises(ValueError, match="Invalid email address"):
            User(id=uuid.uuid4(), email="david_no_shtrudel.com", name="David")

    # ==========================================
    # 2. Name Management (update_name)
    # ==========================================

    def test_user_update_name_success(self, any_user):
        """Happy Path: Successfully updating a user's name."""
        any_user.update_name("New Name")
        assert any_user.name == "New Name"

    def test_user_update_name_to_empty_fails(self, any_user):
        """Sad Path: Validation when updating to an empty or whitespace name."""
        with pytest.raises(ValueError, match="User name cannot be empty"):
            any_user.update_name("  ")

    # ==========================================
    # 3. Token Management (update_push_token)
    # ==========================================

    def test_user_update_push_token_success(self, any_user):
        """Happy Path: Updating the push notification token."""
        new_token = "token_123"
        any_user.update_push_token(new_token)
        assert any_user.push_token == new_token

    def test_user_clear_push_token_on_logout(self, any_user):
        """Happy Path: Clearing the push token when a user logs out."""
        # Setup: User has a token
        any_user.update_push_token("token_to_be_deleted")
        assert any_user.push_token is not None
        
        # Act: Clear it
        any_user.update_push_token(None)
        
        # Assert
        assert any_user.push_token is None