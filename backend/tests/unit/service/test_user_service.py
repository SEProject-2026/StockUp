import pytest
import uuid

@pytest.mark.asyncio
async def test_register_new_user_success(user_service, mock_user_repo):
    """Verify successful registration of a completely new user."""
    # Arrange
    uid = uuid.uuid4()
    email = "new_user@test.com"
    name = "Ori"
    
    # Act
    user = await user_service.register(email=email, user_id=uid, name=name)
    
    # Assert
    assert user.id == uid
    assert user.email == email
    mock_user_repo.save.assert_called_once()

@pytest.mark.asyncio
async def test_register_existing_user_id_returns_current(user_service, mock_user_repo, any_user):
    """Verify that providing an existing ID returns the user without re-saving."""
    # Arrange
    mock_user_repo.get_by_id.return_value = any_user
    
    # Act
    user = await user_service.register(
        email=any_user.email, 
        user_id=any_user.id, 
        name="Different Name"
    )
    
    # Assert
    assert user.id == any_user.id
    mock_user_repo.save.assert_not_called()

@pytest.mark.asyncio
async def test_register_fail_duplicate_email(user_service, mock_user_repo, any_user):
    """Verify email uniqueness check when the User ID is new but email exists."""
    # Arrange
    taken_email = any_user.email
    mock_user_repo.get_by_id.return_value = None 
    mock_user_repo.get_by_email.return_value = any_user
    
    # Act & Assert
    with pytest.raises(ValueError, match="Email already exists"):
        await user_service.register(email=taken_email, user_id=uuid.uuid4(), name="dup")
    
    mock_user_repo.save.assert_not_called()

@pytest.mark.asyncio
async def test_update_name_success(user_service, mock_user_repo, any_user):
    """Verify that a user's display name is updated correctly."""
    # Arrange
    mock_user_repo.get_by_id.return_value = any_user
    new_name = "New Name"
    
    # Act
    await user_service.update_name(any_user.id, new_name)
    
    # Assert
    assert any_user.name == new_name
    mock_user_repo.save.assert_called_once()

@pytest.mark.asyncio
async def test_update_name_fail_user_not_found(user_service, mock_user_repo):
    """Verify error when attempting to update a non-existent user."""
    # Arrange
    mock_user_repo.get_by_id.return_value = None
    
    # Act & Assert
    with pytest.raises(ValueError, match="User not found"):
        await user_service.update_name(uuid.uuid4(), "New Name")

@pytest.mark.asyncio
async def test_update_push_token_success(user_service, mock_user_repo, any_user):
    """Verify that the push notification token is updated for a valid user."""
    # Arrange
    mock_user_repo.get_by_id.return_value = any_user
    new_token = "token_xyz_123"
    
    # Act
    await user_service.update_push_token(any_user.id, new_token)
    
    # Assert
    assert any_user.push_token == new_token
    mock_user_repo.update_push_token.assert_called_with(any_user.id, new_token)

@pytest.mark.asyncio
async def test_update_push_token_fail_user_not_found(user_service, mock_user_repo):
    """Verify error when updating push token for a non-existent user."""
    # Arrange
    mock_user_repo.get_by_id.return_value = None
    
    # Act & Assert
    with pytest.raises(ValueError, match="User not found"):
        await user_service.update_push_token(uuid.uuid4(), "token_123")