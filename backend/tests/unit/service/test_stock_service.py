import pytest
import uuid
import os
from datetime import date, timedelta
from unittest.mock import MagicMock, patch
from src.domain.enums import LocationType, ExpirationType
from src.repositories.catalog_provider import CatalogItem

# --- 1. Product Management (Add / Update / Remove) ---

@pytest.mark.asyncio
async def test_add_product_create_new_success(stock_service, mock_home_repo, mock_product_repo, auth_setup):
    """Verify a non-existent product is created as a new entity."""
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    mock_product_repo.get_by_original_name.return_value = None
    
    product_name = "Cheddar Cheese"
    new_product = await stock_service.add_product(
        name=product_name, user_id=admin.id, home_id=home._id,
        quantity=2, location=LocationType.FRIDGE, barcode="123456"
    )

    assert new_product.original_name == product_name
    assert new_product.total_quantity == 2
    mock_product_repo.save.assert_called_once()

@pytest.mark.asyncio
async def test_add_product_existing_merges_correctly(stock_service, mock_home_repo, mock_product_repo, auth_setup, any_product):
    """Verify that an existing product is updated with a new batch."""
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    any_product.add_item(quantity=5)
    mock_product_repo.get_by_original_name.return_value = any_product

    await stock_service.add_product(
        name=any_product.original_name, user_id=admin.id, home_id=home._id,
        quantity=3, expiration_date=date.today() + timedelta(days=1)
    )

    assert any_product.total_quantity == 8
    assert len(any_product.items) == 2
    mock_product_repo.save.assert_called_with(any_product)

@pytest.mark.asyncio
async def test_add_product_unknown_name_returns_none(stock_service, mock_home_repo, auth_setup, mock_product_repo):
    """Verify that 'Unknown Product' name results in no action."""
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    
    result = await stock_service.add_product(name="Unknown Product", user_id=admin.id, home_id=home._id, quantity=1)

    assert result is None
    mock_product_repo.save.assert_not_called()

@pytest.mark.asyncio
async def test_remove_item_final_deletes_product(stock_service, mock_home_repo, mock_product_repo, auth_setup, any_product):
    """Verify that if the last item is removed, the product is deleted from DB."""
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    any_product.add_item(quantity=1)
    item_id = any_product.items[0].id
    mock_product_repo.get_by_id.return_value = any_product

    result = await stock_service.remove_item(admin.id, home._id, any_product.id, item_id)

    assert result is None
    mock_product_repo.delete.assert_called_with(any_product.id)

@pytest.mark.asyncio
async def test_remove_item_wrong_home_access_denied(stock_service, mock_home_repo, mock_product_repo, auth_setup, any_product):
    """Verify security: user cannot remove product belonging to another home."""
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    
    # Product belongs to a different home ID
    any_product.home_id = uuid.uuid4()
    mock_product_repo.get_by_id.return_value = any_product

    with pytest.raises(ValueError, match="Product not found in this home"):
        await stock_service.remove_item(admin.id, home._id, any_product.id, uuid.uuid4())

# --- 2. Receipt Scanning & Math Logic ---

@pytest.mark.asyncio
@patch("src.services.stock_service.os.path.exists")
async def test_scan_receipt_weight_math_correct(mock_exists, stock_service, mock_home_repo, auth_setup, mock_scanner, mock_catalog_provider):
    """Verify: new_qty = scanned_weight / avg_unit_weight (1.5KG / 0.5KG = 3 units)."""
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    mock_exists.return_value = True
    
    mock_scanner.parse_receipt.return_value = ("Victory", {"999": (1.5, "KG")})
    mock_catalog_provider.get_item_by_barcode.return_value = CatalogItem(
        barcode="999", name="Chicken", weight=0.5, location=LocationType.FRIDGE
    )

    receipt = await stock_service.scan_receipt(admin.id, home._id, ["img.png"])

    assert receipt.items[0].quantity == 3
    assert receipt.items[0].weight == 1.5

@pytest.mark.asyncio
@patch("src.services.stock_service.os.path.exists")
async def test_scan_receipt_unknown_item_defaults_to_one(mock_exists, stock_service, mock_home_repo, auth_setup, mock_scanner, mock_catalog_provider):
    """Verify that unknown scanned items default to 1 unit even if scanned as KG."""
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    mock_exists.return_value = True
    mock_scanner.parse_receipt.return_value = ("Store", {"888": (0.8, "KG")})
    mock_catalog_provider.get_item_by_barcode.return_value = None # Unknown

    receipt = await stock_service.scan_receipt(admin.id, home._id, ["img.jpg"])

    assert receipt.items[0].name == "Unknown Product"
    assert receipt.items[0].quantity == 1

@pytest.mark.asyncio
async def test_scan_receipt_fails_on_empty_files(stock_service, mock_home_repo, auth_setup):
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    with pytest.raises(ValueError, match="must be a non-empty list"):
        await stock_service.scan_receipt(admin.id, home._id, [])

# --- 3. Metadata Updates ---

@pytest.mark.asyncio
async def test_update_item_quantity_success(stock_service, mock_home_repo, mock_product_repo, auth_setup, any_product):
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    any_product.add_item(5)
    item_id = any_product.items[0].id
    mock_product_repo.get_by_id.return_value = any_product

    result = await stock_service.update_item_quantity(admin.id, home._id, any_product.id, item_id, 10)

    assert result.total_quantity == 10
    mock_product_repo.update.assert_called_with(any_product)

@pytest.mark.asyncio
async def test_update_nickname_success(stock_service, mock_home_repo, mock_product_repo, auth_setup, any_product):
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    mock_product_repo.get_by_id.return_value = any_product

    await stock_service.update_nickname(admin.id, home._id, any_product.id, "Favorite Milk")

    assert any_product.nickname == "Favorite Milk"
    mock_product_repo.update.assert_called_once()

# --- 4. Search & Filtering ---

@pytest.mark.asyncio
async def test_search_local_inventory(stock_service, mock_home_repo, mock_product_repo, auth_setup):
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    mock_product_repo.search_by_name.return_value = [MagicMock(original_name="Milk")]

    results = await stock_service.search_product(admin.id, home._id, "Milk")

    assert len(results) == 1
    mock_product_repo.search_by_name.assert_called_once_with(home._id, "Milk")

@pytest.mark.asyncio
async def test_filter_by_expiration_expired(stock_service, mock_home_repo, mock_product_repo, auth_setup, any_product):
    # Arrange
    home, admin = auth_setup
    # Ensure home has a known expiration range
    home._expiration_range = 7 
    mock_home_repo.get_by_id.return_value = home
    
    # Force an EXPIRED item: well in the past to avoid timezone/hour issues
    past_date = date.today() - timedelta(days=10)
    any_product.add_item(quantity=1, expiration_date=past_date)
    
    mock_product_repo.get_all_by_home.return_value = [any_product]

    # Act
    results = await stock_service.filter_by_expiration_type(admin.id, home._id, ExpirationType.EXPIRED)

    # Assert
    assert len(results) == 1
    assert results[0].original_name == any_product.original_name

@pytest.mark.asyncio
async def test_search_external_db_barcode(stock_service, mock_home_repo, auth_setup, mock_catalog_provider):
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    mock_catalog_provider.get_item_by_barcode.return_value = CatalogItem(barcode="111", name="Organic Milk", location=LocationType.FRIDGE)

    result = await stock_service.search_product_by_barcode_external_db(admin.id, home._id, "111")

    assert result.name == "Organic Milk"
    mock_catalog_provider.get_item_by_barcode.assert_called_once_with("111")