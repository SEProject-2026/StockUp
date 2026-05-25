import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.stock_service import StockService
from src.services.user_service import UserService
from src.services.management_service import ManagementService
from src.services.shopping_list_service import ShoppingListService

# --- Infrastructure Mocks (Global for all services) ---

@pytest.fixture(autouse=True)
def mock_notifications():
    """
    Prevents real push notifications. 
    Placed here because only services trigger notifications.
    """
    with patch("src.services.management_service.send_push_notification") as mock_mgmt, \
         patch("src.services.stock_service.send_push_notification") as mock_stock:
        
        mock_mgmt.side_effect = mock_stock
        yield mock_stock

# --- Repository Mocks ---

@pytest.fixture
def mock_user_repo():
    repo = AsyncMock()
    repo.get_by_id.return_value = None
    repo.get_by_email.return_value = None
    return repo

@pytest.fixture
def mock_home_repo():
    repo = AsyncMock()
    repo.get_by_id.return_value = None
    return repo

@pytest.fixture
def mock_product_repo():
    repo = AsyncMock()
    # Ensure these return None by default instead of a new Mock object
    repo.get_by_id.return_value = None
    repo.get_by_original_name.return_value = None
    repo.get_by_barcode.return_value = None
    return repo

@pytest.fixture
def mock_shopping_repo():
    repo = AsyncMock()
    repo.get_by_id.return_value = None
    repo.get_all_by_home.return_value = []
    return repo

@pytest.fixture
def mock_catalog_provider():
    provider = AsyncMock()
    provider.update_weighted_mem_only = MagicMock()
    provider.persist = MagicMock()
    return provider

@pytest.fixture
def mock_scanner():
    return MagicMock()

@pytest.fixture
def mock_receipt_repo():
    """Mock for IReceiptRepository."""
    return AsyncMock()

# --- Service Fixtures (Manual Dependency Injection) ---

@pytest.fixture
def user_service(mock_user_repo):
    return UserService(user_repo=mock_user_repo)

@pytest.fixture
def mgmt_service(mock_home_repo, mock_user_repo):
    return ManagementService(home_repository=mock_home_repo, user_repository=mock_user_repo)

@pytest.fixture
def shopping_list_service(mock_shopping_repo):
    return ShoppingListService(shopping_repo=mock_shopping_repo)

@pytest.fixture
def stock_service(mock_home_repo, mock_product_repo, mock_catalog_provider, mock_user_repo, mock_scanner, mock_receipt_repo):
    return StockService(
        home_repository=mock_home_repo,
        product_repository=mock_product_repo,
        catalog_provider=mock_catalog_provider,
        user_repository=mock_user_repo,
        receipt_scanner=mock_scanner,
        receipt_repository=mock_receipt_repo
    )