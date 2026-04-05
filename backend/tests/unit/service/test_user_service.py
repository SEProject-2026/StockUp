import pytest
import uuid

class TestUserService:

    # ==========================================
    # 1. Registration Logic (register)
    # ==========================================

    @pytest.mark.asyncio
    async def test_register_new_user_success(self, user_service, mock_user_repo):
        """Happy Path: Verify successful registration of a completely new user."""
        uid = uuid.uuid4()
        email = "new_user@test.com"
        name = "Ori"
        
        user = await user_service.register(email=email, user_id=uid, name=name)
        
        assert user.id == uid
        assert user.email == email
        mock_user_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_existing_user_id_returns_current(self, user_service, mock_user_repo, any_user):
        """Happy Path: Providing an existing ID returns the user without re-saving (idempotency)."""
        mock_user_repo.get_by_id.return_value = any_user
        
        user = await user_service.register(
            email=any_user.email, 
            user_id=any_user.id, 
            name="Different Name"
        )
        
        assert user.id == any_user.id
        mock_user_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_register_fail_duplicate_email(self, user_service, mock_user_repo, any_user):
        """Sad Path: Verify email uniqueness check when ID is new but email exists."""
        mock_user_repo.get_by_id.return_value = None 
        mock_user_repo.get_by_email.return_value = any_user
        
        with pytest.raises(ValueError, match="Email already exists"):
            await user_service.register(email=any_user.email, user_id=uuid.uuid4(), name="dup")
        
        mock_user_repo.save.assert_not_called()

    # ==========================================
    # 2. Profile Management (update_name)
    # ==========================================

    @pytest.mark.asyncio
    async def test_update_name_success(self, user_service, mock_user_repo, any_user):
        """Happy Path: User's display name is updated correctly."""
        mock_user_repo.get_by_id.return_value = any_user
        new_name = "New Name"
        
        await user_service.update_name(any_user.id, new_name)
        
        assert any_user.name == new_name
        mock_user_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_name_fail_user_not_found(self, user_service, mock_user_repo):
        """Sad Path: Error when attempting to update a non-existent user."""
        mock_user_repo.get_by_id.return_value = None
        
        with pytest.raises(ValueError, match="User not found"):
            await user_service.update_name(uuid.uuid4(), "New Name")

    # ==========================================
    # 3. Notification Settings (update_push_token)
    # ==========================================

    @pytest.mark.asyncio
    async def test_update_push_token_success(self, user_service, mock_user_repo, any_user):
        """Happy Path: Push notification token is updated via optimized repo method."""
        mock_user_repo.get_by_id.return_value = any_user
        new_token = "token_xyz_123"
        
        await user_service.update_push_token(any_user.id, new_token)
        
        assert any_user.push_token == new_token
        mock_user_repo.update_push_token.assert_called_with(any_user.id, new_token)

    @pytest.mark.asyncio
    async def test_update_push_token_fail_user_not_found(self, user_service, mock_user_repo):
        """Sad Path: Error when updating push token for a non-existent user."""
        mock_user_repo.get_by_id.return_value = None
        
        with pytest.raises(ValueError, match="User not found"):
            await user_service.update_push_token(uuid.uuid4(), "token_123")