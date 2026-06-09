import pytest
from unittest.mock import MagicMock
from src.infrastructure.app_container import AppContainer

def test_app_container_initializes_all_services():
    """Happy Path: Verify the AppContainer can instantiate all services without crashing."""
    
    # יצירת מוק פשוט במקום להשתמש במסד נתונים אמיתי
    db_session_mock = MagicMock()
    
    # 2. Services (These will internally initialize the required repositories)
    user_svc = AppContainer.get_user_service(db_session_mock)
    mgmt_svc = AppContainer.get_management_service(db_session_mock)
    stock_svc = AppContainer.get_stock_service(db_session_mock)
    shop_svc = AppContainer.get_shopping_list_service(db_session_mock)
    rec_svc = AppContainer.get_recommendation_service(db_session_mock)

    assert user_svc is not None
    assert mgmt_svc is not None
    assert stock_svc is not None
    assert shop_svc is not None
    assert rec_svc is not None