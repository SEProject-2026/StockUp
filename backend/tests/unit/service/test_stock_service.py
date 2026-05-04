from unittest.mock import MagicMock
import pytest
import uuid
from datetime import date, timedelta
from src.domain.receipt.receipt import ReceiptDTO, ReceiptItemDTO
from src.domain.product.product import Product
from src.repositories.catalog_provider import CatalogItem
from src.domain.enums import ExpirationType, LocationType

# ==========================================
# 1. Tests for add_product
# ==========================================

@pytest.mark.asyncio
async def test_add_product_success(stock_service, mock_home_repo, mock_product_repo, auth_setup):
    """
    Scenario: Adding a completely new product to a home.
    Verify: 
    1. The product is created with correct attributes.
    2. Defaults (like LocationType.OTHER) are applied if not provided.
    3. The product is persisted via the repository.
    """
    # Arrange
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    mock_product_repo.get_by_original_name.return_value = None
    
    product_name = "Milk"
    barcode = "729000"
    nickname = "My Snack"

    # Act
    product = await stock_service.add_product(
        name=product_name,
        user_id=admin.id,
        home_id=home._id, # Accessing domain attribute _id
        quantity=5,
        barcode=barcode,
        expiration_date=None, 
        location=None, # Should trigger default logic
        nickname=nickname
    )
    
    # Assert result attributes
    assert product.original_name == product_name
    assert product.nickname == nickname
    assert product.total_quantity == 5
    assert len(product.items) == 1
    # Verify domain default logic was applied
    assert product.items[0].location == LocationType.OTHER

    # Assert persistence
    mock_product_repo.save.assert_called_once()
    saved_product = mock_product_repo.save.call_args[0][0]
    assert saved_product.id == product.id


@pytest.mark.asyncio
async def test_add_product_merges_with_existing(stock_service, mock_home_repo, mock_product_repo, auth_setup, any_product):
    """
    Scenario: Adding a product that already exists in the home inventory.
    Verify: The service retrieves the existing entity and merges the new quantity.
    """
    # Arrange
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    
    # Setup: Product already has 10 units in the Fridge
    any_product.add_item(quantity=10, location=LocationType.FRIDGE)
    mock_product_repo.get_by_original_name.return_value = any_product
    
    initial_total = any_product.total_quantity

    # Act: Add 5 more units to the same location
    updated_product = await stock_service.add_product(
        name=any_product.original_name,
        user_id=admin.id,
        home_id=home._id,
        quantity=5,
        location=LocationType.FRIDGE
    )

    # Assert
    assert updated_product.total_quantity == initial_total + 5
    assert len(updated_product.items) == 1 # Merged into the same batch
    mock_product_repo.save.assert_called_once_with(any_product)


@pytest.mark.asyncio
async def test_add_product_fails_if_home_not_found(stock_service, mock_home_repo,mock_product_repo, auth_setup):
    """
    Scenario: User attempts to add a product to a non-existent Home ID.
    Verify: Service raises ValueError and stops execution.
    """
    # Arrange
    _, admin = auth_setup
    fake_home_id = uuid.uuid4()
    mock_home_repo.get_by_id.return_value = None # Simulate missing home
    
    # Act & Assert
    with pytest.raises(ValueError, match="Home retrieval failed"): 
        await stock_service.add_product(
            name="Milk", 
            user_id=admin.id, 
            home_id=fake_home_id, 
            quantity=1
        )
    
    # Verify no data was saved
    mock_product_repo.save.assert_not_called()


@pytest.mark.asyncio
async def test_add_product_invalid_quantity_fails(stock_service, mock_home_repo, auth_setup):
    """
    Scenario: User provides a zero or negative quantity.
    Verify: Domain/Service validation catches the error.
    """
    # Arrange
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home

    # Act & Assert
    with pytest.raises(ValueError, match="must be positive"):
        await stock_service.add_product(
            name="Bread",
            user_id=admin.id,
            home_id=home._id,
            quantity=0
        )

@pytest.mark.asyncio
async def test_add_same_product_accumulates_quantity(stock_service, mock_home_repo, mock_product_repo, auth_setup):
    """
    Scenario: 
    1. Add items -> New product created.
    2. Add items (same location/date) -> Merges into existing batch.
    3. Add items (different date) -> Creates a second batch within same product.
    """
    # Arrange
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    barcode = "111"
    
    # 1. Add first batch (No Date, Pantry)
    mock_product_repo.get_by_original_name.return_value = None # Product doesn't exist yet
    
    product = await stock_service.add_product(
        name="Product", user_id=admin.id, home_id=home._id, 
        quantity=3, barcode=barcode, location=LocationType.PANTRY
    )
    
    # 2. Add second batch (Same Location, Same Date) -> MERGE
    # Setup mock to return the product we just created
    mock_product_repo.get_by_original_name.return_value = product
    
    await stock_service.add_product(
        name="Product", user_id=admin.id, home_id=home._id, 
        quantity=3, barcode=barcode, location=LocationType.PANTRY
    )
    
    # Intermediate Assertions
    assert product.total_quantity == 6
    assert len(product.items) == 1 # Verified: Merged into 1 batch
    
    # 3. Add third batch (Different Date) -> NEW BATCH
    future_date = date.today() + timedelta(days=5)
    await stock_service.add_product(
        name="Product", user_id=admin.id, home_id=home._id, 
        quantity=3, barcode=barcode, location=LocationType.PANTRY,
        expiration_date=future_date
    )

    # Final Assertions
    assert product.total_quantity == 9
    assert len(product.items) == 2 # Verified: Two distinct batches
    
    item_no_date = next(i for i in product.items if i.expiration_date is None)
    item_with_date = next(i for i in product.items if i.expiration_date == future_date)
    
    assert item_no_date.quantity == 6
    assert item_with_date.quantity == 3


# ==========================================
# 2. Tests for remove_item (Cleanup & Persistence)
# ==========================================

@pytest.mark.asyncio
async def test_remove_item_partial_update(stock_service, mock_home_repo, mock_product_repo, auth_setup, any_product):
    """
    Scenario: Product has 2 batches. We remove one specific batch.
    Verify: Product remains, quantity decreases, correct item persists in DB.
    """
    # Arrange
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    
    # Setup: any_product with 2 batches (Fridge & Pantry)
    any_product.add_item(quantity=5, location=LocationType.FRIDGE)
    any_product.add_item(quantity=3, location=LocationType.PANTRY)
    
    mock_product_repo.get_by_id.return_value = any_product
    
    item_to_remove = next(i for i in any_product.items if i.location == LocationType.FRIDGE)
    item_to_keep = next(i for i in any_product.items if i.location == LocationType.PANTRY)

    # Act
    updated_product = await stock_service.remove_item(
        admin.id, home._id, any_product.id, item_to_remove.id
    )

    # Assert
    assert updated_product is not None
    assert updated_product.total_quantity == 3
    assert len(updated_product.items) == 1
    assert updated_product.items[0].id == item_to_keep.id
    
    # Verify persistence: repository.update called, NOT delete
    mock_product_repo.update.assert_called_once_with(any_product)
    mock_product_repo.delete.assert_not_called()


@pytest.mark.asyncio
async def test_remove_item_full_deletion(stock_service, mock_home_repo, mock_product_repo, auth_setup, any_product):
    """
    Scenario: Product has only 1 item. Removing it should delete the product entirely.
    """
    # Arrange
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    
    any_product.add_item(quantity=5)
    item_id = any_product.items[0].id
    mock_product_repo.get_by_id.return_value = any_product

    # Act
    result = await stock_service.remove_item(admin.id, home._id, any_product.id, item_id)

    # Assert
    assert result is None # Service returns None to indicate full deletion
    mock_product_repo.delete.assert_called_once_with(any_product.id)
    mock_product_repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_remove_item_fails_invalid_id(stock_service, mock_home_repo, mock_product_repo, auth_setup, any_product):
    """
    Scenario: Attempting to remove an item ID that doesn't exist in the product.
    """
    # Arrange
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    
    any_product.add_item(quantity=5)
    mock_product_repo.get_by_id.return_value = any_product
    
    fake_item_id = uuid.uuid4()

    # Act & Assert
    with pytest.raises(ValueError, match="not found"):
        await stock_service.remove_item(admin.id, home._id, any_product.id, fake_item_id)

# ==========================================
# 3. Tests for update_item_quantity
# ==========================================

@pytest.mark.asyncio
async def test_update_item_quantity_success(stock_service, mock_home_repo, mock_product_repo, auth_setup, any_product):
    """
    Scenario: User edits the quantity of a specific batch (e.g., from 12 to 6).
    Verify: The quantity updates correctly in the entity and the repository is updated.
    """
    # Arrange
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    
    # Setup product with 12 items
    any_product.add_item(quantity=12, location=LocationType.FRIDGE)
    item_id = any_product.items[0].id
    mock_product_repo.get_by_id.return_value = any_product

    # Act
    updated_product = await stock_service.update_item_quantity(
        user_id=admin.id,
        home_id=home._id,
        product_id=any_product.id,
        item_id=item_id,
        new_quantity=6
    )
    
    # Assert
    assert updated_product.items[0].quantity == 6
    assert updated_product.total_quantity == 6
    mock_product_repo.update.assert_called_once_with(any_product)


@pytest.mark.asyncio
async def test_update_item_quantity_to_zero_removes_item(stock_service, mock_home_repo, mock_product_repo, auth_setup, any_product):
    """
    Scenario: Product has 2 batches. Update one batch to quantity 0.
    Verify: The specific batch is removed, but the Product remains with the other batch.
    """
    # Arrange
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    
    # Setup: 2 batches (Fridge and Pantry)
    any_product.add_item(quantity=5, location=LocationType.FRIDGE)
    any_product.add_item(quantity=3, location=LocationType.PANTRY)
    
    item_fridge = next(i for i in any_product.items if i.location == LocationType.FRIDGE)
    mock_product_repo.get_by_id.return_value = any_product

    # Act: Update Fridge batch to 0
    updated_product = await stock_service.update_item_quantity(
        user_id=admin.id,
        home_id=home._id,
        product_id=any_product.id,
        item_id=item_fridge.id,
        new_quantity=0
    )
    
    # Assert
    assert updated_product is not None
    assert updated_product.total_quantity == 3 # Only Pantry remains
    assert len(updated_product.items) == 1
    assert updated_product.items[0].location == LocationType.PANTRY
    mock_product_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_update_item_quantity_to_zero_deletes_product_if_last(stock_service, mock_home_repo, mock_product_repo, auth_setup, any_product):
    """
    Scenario: Product has only 1 batch. Update it to 0.
    Verify: The Product is completely DELETED from DB (Cleanup logic).
    """
    # Arrange
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    
    any_product.add_item(quantity=5)
    item_id = any_product.items[0].id
    mock_product_repo.get_by_id.return_value = any_product

    # Act
    result = await stock_service.update_item_quantity(
        user_id=admin.id,
        home_id=home._id,
        product_id=any_product.id,
        item_id=item_id,
        new_quantity=0
    )
    
    # Assert
    assert result is None # Service returns None on deletion
    mock_product_repo.delete.assert_called_once_with(any_product.id)
    mock_product_repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_update_item_quantity_fails_negative(stock_service, mock_home_repo, mock_product_repo, auth_setup, any_product):
    """
    Scenario: User tries to set a negative quantity.
    Verify: ValueError is raised from the Domain level.
    """
    # Arrange
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    
    any_product.add_item(quantity=12)
    item_id = any_product.items[0].id
    mock_product_repo.get_by_id.return_value = any_product

    # Act & Assert
    with pytest.raises(ValueError, match="cannot be negative"):
        await stock_service.update_item_quantity(
            user_id=admin.id,
            home_id=home._id,
            product_id=any_product.id,
            item_id=item_id,
            new_quantity=-5
        )


@pytest.mark.asyncio
async def test_update_item_quantity_fails_invalid_item_id(stock_service, mock_home_repo, mock_product_repo, auth_setup, any_product):
    """
    Scenario: User tries to update an item ID that does not exist in the product.
    Verify: ValueError is raised.
    """
    # Arrange
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    
    any_product.add_item(quantity=12)
    mock_product_repo.get_by_id.return_value = any_product
    
    fake_id = uuid.uuid4()
    
    # Act & Assert
    with pytest.raises(ValueError, match="not found"):
        await stock_service.update_item_quantity(
            admin.id, home._id, any_product.id, fake_id, 5
        )

# ==========================================
# 4. Tests for update_item_date
# ==========================================

@pytest.mark.asyncio
async def test_update_item_date_simple_change(stock_service, mock_home_repo, mock_product_repo, auth_setup, any_product):
    """
    Scenario: User changes expiration date when no other items exist.
    Verify: A simple field update occurs and is persisted.
    """
    # Arrange
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    old_date = date(2025, 1, 1)
    new_date = date(2025, 2, 1)
    
    # Setup product with one batch
    any_product.add_item(quantity=1, expiration_date=old_date)
    item_id = any_product.items[0].id
    mock_product_repo.get_by_id.return_value = any_product

    # Act
    updated_product = await stock_service.update_item_date(
        user_id=admin.id,
        home_id=home._id,
        product_id=any_product.id,
        item_id=item_id,
        new_date=new_date
    )
    
    # Assert
    assert len(updated_product.items) == 1
    assert updated_product.items[0].expiration_date == new_date
    mock_product_repo.update.assert_called_once_with(any_product)


@pytest.mark.asyncio
async def test_update_item_date_merges_duplicates(stock_service, mock_home_repo, mock_product_repo, auth_setup, any_product):
    """
    Scenario: Changing a batch date to match an existing batch's date.
    Verify: The two batches merge into one, summing their quantities.
    """
    # Arrange
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    date_1 = date(2025, 1, 1)
    date_2 = date(2025, 2, 1)
    
    # Setup: Two batches in Fridge with different dates
    any_product.add_item(quantity=2, expiration_date=date_1, location=LocationType.FRIDGE)
    any_product.add_item(quantity=3, expiration_date=date_2, location=LocationType.FRIDGE)
    
    item_to_change = next(i for i in any_product.items if i.expiration_date == date_2)
    mock_product_repo.get_by_id.return_value = any_product

    # Act: Change date_2 to match date_1
    updated_product = await stock_service.update_item_date(
        admin.id, home._id, any_product.id, item_to_change.id, date_1
    )
    
    # Assert
    assert len(updated_product.items) == 1 # Merged
    assert updated_product.items[0].expiration_date == date_1
    assert updated_product.total_quantity == 5 # 2 + 3
    mock_product_repo.update.assert_called_once()


# ==========================================
# 5. Tests for update_item_location
# ==========================================

@pytest.mark.asyncio
async def test_update_item_location_success(stock_service, mock_home_repo, mock_product_repo, auth_setup, any_product):
    """
    Scenario: Move an item from PANTRY to FRIDGE.
    Verify: Location updates and change is persisted.
    """
    # Arrange
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    any_product.add_item(quantity=2, location=LocationType.PANTRY)
    item_id = any_product.items[0].id
    mock_product_repo.get_by_id.return_value = any_product

    # Act
    updated_product = await stock_service.update_item_location(
        admin.id, home._id, any_product.id, item_id, LocationType.FRIDGE
    )
    
    # Assert
    assert updated_product.items[0].location == LocationType.FRIDGE
    mock_product_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_update_item_location_merges_duplicates(stock_service, mock_home_repo, mock_product_repo, auth_setup, any_product):
    """
    Scenario: Moving an item to a location that already contains an identical batch.
    Verify: The items merge instead of creating a duplicate entry in the same location.
    """
    # Arrange
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    
    # Setup: 2 units in Fridge, 3 in Pantry (all same expiration)
    any_product.add_item(quantity=2, location=LocationType.FRIDGE)
    any_product.add_item(quantity=3, location=LocationType.PANTRY)
    
    item_pantry = next(i for i in any_product.items if i.location == LocationType.PANTRY)
    mock_product_repo.get_by_id.return_value = any_product

    # Act: Move Pantry batch to Fridge
    updated_product = await stock_service.update_item_location(
        admin.id, home._id, any_product.id, item_pantry.id, LocationType.FRIDGE
    )
    
    # Assert
    assert len(updated_product.items) == 1
    assert updated_product.items[0].location == LocationType.FRIDGE
    assert updated_product.items[0].quantity == 5 # 2 + 3
    mock_product_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_update_item_location_fails_invalid_item_id(stock_service, mock_home_repo, mock_product_repo, auth_setup, any_product):
    """
    Scenario: Attempt to move a non-existent item ID.
    Verify: ValueError is raised.
    """
    # Arrange
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    any_product.add_item(quantity=2)
    mock_product_repo.get_by_id.return_value = any_product
    
    fake_item_id = uuid.uuid4()

    # Act & Assert
    with pytest.raises(ValueError, match="not found"):
        await stock_service.update_item_location(
            admin.id, home._id, any_product.id, fake_item_id, LocationType.FRIDGE
        )

# ==========================================
# 5. Tests for update_nickname
# ==========================================

@pytest.mark.asyncio
async def test_update_nickname_success(stock_service, mock_home_repo, mock_product_repo, auth_setup, any_product):
    """
    Scenario: User updates nickname from None to 'My Milk'.
    Verify: Nickname updates correctly while the original product name remains unchanged.
    """
    # Arrange
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    
    # Setup product: Original name "Milk", no initial nickname
    any_product.original_name = "Milk"
    any_product.nickname = None
    mock_product_repo.get_by_id.return_value = any_product

    # Act: Update Nickname
    updated_product = await stock_service.update_nickname(
        user_id=admin.id,
        home_id=home._id,
        product_id=any_product.id,
        new_nickname="My Milk"
    )
    
    # Assert
    assert updated_product.nickname == "My Milk"
    assert updated_product.original_name == "Milk" # Verify original name is untouched
    
    # Verify Persistence
    mock_product_repo.update.assert_called_once_with(any_product)


@pytest.mark.asyncio
async def test_update_nickname_overwrites_existing(stock_service, mock_home_repo, mock_product_repo, auth_setup, any_product):
    """
    Scenario: User changes an existing nickname to a new one.
    Verify: The new nickname successfully overwrites the old one.
    """
    # Arrange
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    
    # Setup product with an existing nickname
    any_product.nickname = "Old Nick"
    mock_product_repo.get_by_id.return_value = any_product

    # Act
    updated_product = await stock_service.update_nickname(
        user_id=admin.id,
        home_id=home._id,
        product_id=any_product.id,
        new_nickname="New Nick"
    )
    
    # Assert
    assert updated_product.nickname == "New Nick"
    mock_product_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_update_nickname_fails_product_not_found(stock_service, mock_home_repo, mock_product_repo, auth_setup):
    """
    Scenario: Attempt to update nickname for a non-existent product ID.
    Verify: ValueError is raised.
    """
    # Arrange
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    mock_product_repo.get_by_id.return_value = None # Product missing

    # Act & Assert
    with pytest.raises(ValueError, match="Product not found"):
        await stock_service.update_nickname(
            user_id=admin.id,
            home_id=home._id,
            product_id=uuid.uuid4(),
            new_nickname="Ghost Milk"
        )

# ==========================================
# 6. Tests for Product Filtering (Location & Expiration)
# ==========================================


@pytest.mark.asyncio
async def test_filter_products_delegates_to_repo(stock_service, mock_home_repo, mock_product_repo, auth_setup, any_product):
    """
    Scenario: User filters by location and expiration.
    Verify: The service fetches warning_days from the home and passes all 
            parameters correctly to the product repository.
    """
    # Arrange
    home, admin = auth_setup
    home._expiration_range = 10 # Set custom warning days
    mock_home_repo.get_by_id.return_value = home
    
    # We mock the REPO'S filter method to return our product
    mock_product_repo.filter_products.return_value = [any_product]

    # Act
    results = await stock_service.filter_products(
        user_id=admin.id, 
        home_id=home._id, 
        location=LocationType.FRIDGE,
        expiration_type=ExpirationType.EXPIRED
    )

    # Assert
    assert len(results) == 1
    assert results[0] == any_product
    
    # Verify the service passed the correct 'warning_days' from the home setup
    mock_product_repo.filter_products.assert_called_once_with(
        home._id,
        query_text=None,
        location=LocationType.FRIDGE,
        expiration_type=ExpirationType.EXPIRED,
        warning_days=10 
    )

@pytest.mark.asyncio
async def test_filter_products_with_query_string(stock_service, mock_home_repo, mock_product_repo, auth_setup):
    """
    Scenario: User searches for "Milk" via the filter method.
    Verify: The query string is passed to the repository.
    """
    # Arrange
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    mock_product_repo.filter_products.return_value = []

    # Act
    await stock_service.filter_products(
        user_id=admin.id, 
        home_id=home._id, 
        query="Milk"
    )

    # Assert
    mock_product_repo.filter_products.assert_called_once_with(
        home._id,
        query_text="Milk",
        location=None,
        expiration_type=None,
        warning_days=home._expiration_range
    )


# ==========================================
# 7. External Catalog & Inventory Retrieval
# ==========================================

@pytest.mark.asyncio
async def test_search_product_by_name_external_db_success(stock_service, mock_home_repo, mock_catalog_provider, auth_setup):
    """
    Scenario: Search in external DB by name.
    Verify: The service delegates to the catalog provider and returns mapped items.
    """
    # Arrange
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    
    # Setup Mock CatalogItem
    mock_item = MagicMock(spec=CatalogItem) 
    mock_item.name = "Bamba"
    mock_item.barcode = "9001"
    
    mock_catalog_provider.search_items_by_name.return_value = [mock_item]

    # Act
    results = await stock_service.search_product_by_name_external_db(
        admin.id, home._id, "Bamba"
    )

    # Assert
    assert len(results) == 1
    assert results[0].name == "Bamba"
    mock_catalog_provider.search_items_by_name.assert_called_once_with("Bamba")


@pytest.mark.asyncio
async def test_search_product_by_barcode_external_db_success(stock_service, mock_home_repo, mock_catalog_provider, auth_setup):
    """
    Scenario: Search in external DB by a specific barcode.
    Verify: Returns the correct single item from the provider.
    """
    # Arrange
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    
    mock_item = MagicMock(spec=CatalogItem)
    mock_item.name = "Milk"
    mock_item.barcode = "123456"
    
    mock_catalog_provider.get_item_by_barcode.return_value = mock_item

    # Act
    result = await stock_service.search_product_by_barcode_external_db(
        admin.id, home._id, "123456"
    )

    # Assert
    assert result is not None
    assert result.name == "Milk"
    assert result.barcode == "123456"
    mock_catalog_provider.get_item_by_barcode.assert_called_once_with("123456")


@pytest.mark.asyncio
async def test_search_product_by_barcode_external_db_not_found(stock_service, mock_home_repo, mock_catalog_provider, auth_setup):
    """
    Scenario: Barcode does not exist in the external catalog.
    Verify: Service returns None gracefully.
    """
    # Arrange
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    mock_catalog_provider.get_item_by_barcode.return_value = None

    # Act
    result = await stock_service.search_product_by_barcode_external_db(
        admin.id, home._id, "999999"
    )

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_home_products_success(stock_service, mock_home_repo, mock_product_repo, auth_setup, any_product):
    """
    Scenario: Retrieve the full inventory for a home.
    Verify: Returns a list of Product entities belonging to the home.
    """
    # Arrange
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home

    # Setup products
    product1 = any_product
    product1.original_name = "Milk"

    product2 = MagicMock(spec=Product)
    product2.original_name = "Bread"

    # FIX: Use list_all_by_home to match the Service's call
    mock_product_repo.list_all_by_home.return_value = [product1, product2]

    # Act
    products = await stock_service.get_home_products(admin.id, home._id)

    # Assert
    assert len(products) == 2
    names = [p.original_name for p in products]
    assert "Milk" in names
    assert "Bread" in names
    # Verify the specific repository method was called
    mock_product_repo.list_all_by_home.assert_called_once_with(home._id)

# ==========================================
# 9. Tests for validate_receipt + commit_receipt
# ==========================================

@pytest.mark.asyncio
async def test_validate_receipt_returns_known_item_count(stock_service, mock_home_repo, auth_setup):
    """
    Scenario: Validating a receipt with mixed known and unknown items.
    Verify: Returns count of known items only, performs access check.
    """
    # Arrange
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home

    items = [
        ReceiptItemDTO(name="Milk", quantity=2.0, barcode="111"),
        ReceiptItemDTO(name="Unknown Product", quantity=1.0, barcode="999"),
        ReceiptItemDTO(name="Bread", quantity=1.0, barcode="222")
    ]
    receipt_dto = ReceiptDTO(id=uuid.uuid4(), home_id=home._id, user_id=admin.id, items=items)

    # Act
    count = await stock_service.validate_receipt(receipt_dto)

    # Assert
    assert count == 2


@pytest.mark.asyncio
async def test_commit_receipt_success(stock_service, mock_home_repo, mock_product_repo, auth_setup):
    """
    Scenario: Committing a receipt with multiple items.
    Verify: The service uses the repository's receipt-optimized bulk save.
    """
    # Arrange
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home
    
    # No existing products
    mock_product_repo.list_all_by_home.return_value = []

    items = [
        ReceiptItemDTO(name="Milk", quantity=2.0, barcode="111"),
        ReceiptItemDTO(name="Bread", quantity=1.0, barcode="222")
    ]
    receipt_dto = ReceiptDTO(id=uuid.uuid4(), home_id=home._id, user_id=admin.id, items=items)

    # Act
    await stock_service._commit_receipt_internal(receipt_dto, 2)

    # Assert
    mock_product_repo.save_all_receipt.assert_called_once()
    call_args = mock_product_repo.save_all_receipt.call_args
    new_products = call_args.kwargs.get("new_products") or call_args[1].get("new_products") if call_args[1] else call_args[0][0]
    
    # Both products are new (didn't exist before)
    assert len(new_products) == 2


@pytest.mark.asyncio
async def test_commit_receipt_merges_with_existing_inventory(stock_service, mock_home_repo, mock_product_repo, auth_setup, any_product):
    """
    Scenario: Receipt contains an item that already exists in the inventory.
    Verify: The service finds the existing entity and merges quantities.
    """
    # Arrange
    home, admin = auth_setup
    mock_home_repo.get_by_id.return_value = home

    # 1. Setup the existing product object using Domain methods
    product_name = "Butter"
    product_barcode = "BT-99"
    
    # We set the attributes and add the initial item
    any_product.original_name = product_name
    any_product.home_id = home._id
    any_product.add_item(quantity=1, location=LocationType.FRIDGE)
    
    # 2. Mock lookup methods
    mock_product_repo.list_all_by_home.return_value = [any_product]

    # 3. Prepare the Receipt DTO
    receipt_dto = ReceiptDTO(
        id=uuid.uuid4(),
        home_id=home._id,
        user_id=admin.id,
        items=[
            ReceiptItemDTO(
                name=product_name, 
                quantity=3.0, 
                barcode=product_barcode,
                location=LocationType.FRIDGE
            )
        ]
    )

    # Act
    await stock_service._commit_receipt_internal(receipt_dto, 1)

    # Assert
    # Initial 1 + Receipt 3 = 4
    assert any_product.total_quantity == 4
    mock_product_repo.save_all_receipt.assert_called_once()

@pytest.mark.asyncio
async def test_validate_receipt_fails_unauthorized(stock_service, mock_home_repo, auth_setup):
    """
    Scenario: Commit a receipt to a home where the user is not a member.
    Verify: ValueError is raised and no items are processed.
    """
    # Arrange
    home, _ = auth_setup
    stranger_id = uuid.uuid4()
    mock_home_repo.get_by_id.return_value = home # Home exists, but stranger is not a member

    receipt_dto = ReceiptDTO(
        id=uuid.uuid4(), home_id=home._id, user_id=stranger_id,
        items=[ReceiptItemDTO(name="Milk", quantity=1.0)]
    )

    # Act & Assert
    with pytest.raises(ValueError, match="User is not a member"):
        await stock_service.validate_receipt(receipt_dto)