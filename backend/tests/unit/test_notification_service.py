import pytest
from unittest.mock import patch, MagicMock
from exponent_server_sdk import PushServerError

from src.services.notification_service import send_push_notification

class TestNotificationService:

    @patch('src.services.notification_service.PushClient')
    def test_send_push_notification_success(self, mock_push_client):
        mock_instance = mock_push_client.return_value
        mock_response = MagicMock()
        mock_response.status = "ok"
        mock_instance.publish.return_value = mock_response

        token = "ExponentPushToken[mock_token_123]"
        response = send_push_notification(token, "Test Title", "Test Message")

        assert response is not None
        assert response.status == "ok"
        
        mock_instance.publish.assert_called_once()

    @patch('src.services.notification_service.PushClient')
    def test_send_push_notification_server_error(self, mock_push_client):
        mock_instance = mock_push_client.return_value
        mock_instance.publish.side_effect = PushServerError("Expo servers are down", response=None)

        token = "ExponentPushToken[mock_token_123]"
        response = send_push_notification(token, "Test Title", "Test Message")

        assert response is None