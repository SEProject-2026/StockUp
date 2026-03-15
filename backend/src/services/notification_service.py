from exponent_server_sdk import (
    PushClient,
    PushMessage,
    PushServerError,
)
from src.infrastructure.logger import app_logger

def send_push_notification(token: str, title: str, message: str, data: dict = None, category_id: str = None):
    """
    Send a push notification to a specific device using Expo's Push API.
    """
    try:
        response = PushClient().publish(
            PushMessage(
                to=token,
                title=title,
                body=message,
                data=data,
                category=category_id
            )
        )
        app_logger.info(f"Push notification sent successfully to {token}")
        return response
        
    except PushServerError as exc:
        app_logger.error(f"Expo Server Error: {exc}")
        
    except ValueError as exc:
        app_logger.error(f"Invalid Push Token format: {exc}")
        
    except Exception as exc:
        app_logger.error(f"Failed to send push notification: {exc}")

