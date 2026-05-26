import pytest
from fastapi import HTTPException
from unittest.mock import patch, MagicMock
from src.api.security import get_current_user_id

@pytest.mark.asyncio
async def test_get_current_user_id_success():
    """Happy Path: Valid token returns user ID."""
    mock_auth = MagicMock()
    mock_auth.verify_token.return_value = "550e8400-e29b-41d4-a716-446655440000"

    with patch("src.infrastructure.app_container.AppContainer.get_auth_provider", return_value=mock_auth):
        mock_cred = MagicMock()
        mock_cred.credentials = "valid_token"

        user_id = await get_current_user_id(mock_cred)
        assert str(user_id) == "550e8400-e29b-41d4-a716-446655440000"

@pytest.mark.asyncio
async def test_get_current_user_id_invalid_token_fails():
    """Sad Path: Invalid token raises 401."""
    mock_auth = MagicMock()
    mock_auth.verify_token.return_value = None # מדמה טוקן לא חוקי
    
    with patch("src.infrastructure.app_container.AppContainer.get_auth_provider", return_value=mock_auth):
        mock_cred = MagicMock()
        mock_cred.credentials = "invalid_token"
        
        with pytest.raises(HTTPException) as exc:
            await get_current_user_id(mock_cred)
            
        assert exc.value.status_code == 401