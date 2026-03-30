from unittest.mock import AsyncMock, MagicMock
import pytest
from uuid import UUID, uuid4
from datetime import date, timedelta
from src.domain.product.product import Product
from tests1.container import testing_container
from src.domain.enums import ExpirationType, LocationType, UnitType

# --- Helper Functions ---

def setup_function():
    testing_container.activate_memory_mode()
    """
    Reset state before every test.
    """
    testing_container.reset_state()

async def setup_env():
    """
    Creates environment for Service Testing.
    """
    # 1. Register User
    fake_uid = "550e8400-e29b-41d4-a716-446655440000"
    user = await testing_container.user_service.register(
        user_id=fake_uid,
        email="stock_test@test.com",
        name="Stock User"
    )
    
    # 2. Create Home
    home = await testing_container.management_service.create_home(user.id, "My Stock Home")
    
    testing_container.stock_service._catalog_provider = MagicMock()
    
    return user.id, home.get_id()

# --- Tests for add_product ---

@pytest.mark.asyncio
async def test_add_product_success():
    """
    Scenario: Adding a completely new product.
    """
    user_id, home_id = await setup_env()
    
    # Act
    product = await testing_container.stock_service.add_product(
        name="Milk",
        user_id=user_id,
        home_id=home_id,
        quantity=5,
        barcode="729000",
        expiration_date=None, 
        location=None, # Should default to OTHER
        nickname="My Snack"
    )
    
    # Assert return value
    assert product.original_name == "Milk"
    assert product.nickname == "My Snack"
    assert product.total_quantity == 5
    assert len(product.items) == 1
    assert product.items[0].location == LocationType.OTHER  # Default check

    # Assert persistence in Repo
    products_in_db = await testing_container.stock_repo.list_all_by_home(home_id)
    assert len(products_in_db) == 1
    assert products_in_db[0].id == product.id


@pytest.mark.asyncio
async def test_add_product_fails_if_home_not_found():
    """
    Scenario: Trying to add product to a non-existent home.
    """
    user_id, _ = await setup_env()
    fake_home_id = uuid4()
    
    # Assuming _check_access validates home existence
    with pytest.raises(ValueError, match="Home retrieval failed"): 
        await testing_container.stock_service.add_product(
            name="Milk", 
            user_id=user_id, 
            home_id=fake_home_id, 
            quantity=1, 
            barcode="123", 
            expiration_date=None, 
            location=None, 
            nickname=None
        )


@pytest.mark.asyncio
async def test_add_product_fails_on_negative_quantity():
    """
    Scenario: Validation check for negative quantity.
    """
    user_id, home_id = await setup_env()
    
    with pytest.raises(ValueError, match="Quantity to add must be positive"):
        await testing_container.stock_service.add_product(
            name="Milk", 
            user_id=user_id, 
            home_id=home_id, 
            quantity=-1, 
            barcode="123", 
            expiration_date=None, 
            location=None, 
            nickname=None
        )


@pytest.mark.asyncio
async def test_add_same_product_accumulates_quantity():
    """
    Scenario: 
    1. Add 3 items.
    2. Add 3 items (same location/date) -> Should merge.
    3. Add 3 items (different date) -> Should create new batch.
    """
    user_id, home_id = await setup_env()
    barcode = "111"
    
    # 1. Add 3 (Default Location, No Date)
    await testing_container.stock_service.add_product(
        name="Product", 
        user_id=user_id, 
        home_id=home_id, 
        quantity=3, 
        barcode=barcode, 
        expiration_date=None, 
        location=LocationType.PANTRY, 
        nickname=None
    )
    
    # 2. Add 3 more (Same Location, Same Date) -> MERGE
    await testing_container.stock_service.add_product(
        name="Product", 
        user_id=user_id, 
        home_id=home_id, 
        quantity=3, 
        barcode=barcode, 
        expiration_date=None, 
        location=LocationType.PANTRY, 
        nickname=None
    )
    
    # Check intermediate state
    products = await testing_container.stock_repo.list_all_by_home(home_id)
    assert len(products) == 1
    prod = products[0]
    assert prod.total_quantity == 6
    assert len(prod.items) == 1 # Still 1 batch
    
    # 3. Add 3 with DATE (Different batch)
    future_date = date.today() + timedelta(days=5)
    await testing_container.stock_service.add_product(
        name="Product", 
        user_id=user_id, 
        home_id=home_id, 
        quantity=3, 
        barcode=barcode, 
        expiration_date=future_date, 
        location=LocationType.PANTRY, 
        nickname=None
    )

    # Final Check
    products = await testing_container.stock_repo.list_all_by_home(home_id)
    prod = products[0]
    
    assert prod.total_quantity == 9 # 6 + 3
    assert len(prod.items) == 2     # Two distinct batches
    
    # Verify quantities per batch
    item_no_date = next(i for i in prod.items if i.expiration_date is None)
    item_with_date = next(i for i in prod.items if i.expiration_date == future_date)
    
    assert item_no_date.quantity == 6
    assert item_with_date.quantity == 3



# --- Tests for remove_item ---

@pytest.mark.asyncio
async def test_remove_item_partial_update():
    """
    Scenario: Product has 2 batches (items). We remove one specific batch.
    Expected: Product remains in DB, total quantity decreases, specific item is gone.
    """
    user_id, home_id = await setup_env()
    
    # 1. Setup: Add product with 2 different batches
    # Batch 1: Fridge
    product = await testing_container.stock_service.add_product(
        "Milk", user_id, home_id, 5, "111", None, LocationType.FRIDGE, None
    )
    # Batch 2: Pantry (creates a new Item ID)
    product = await testing_container.stock_service.add_product(
        "Milk", user_id, home_id, 3, "111", None, LocationType.PANTRY, None
    )
    
    assert len(product.items) == 2
    assert product.total_quantity == 8
    
    # Identify the item to remove (The Fridge one)
    item_to_remove = next(i for i in product.items if i.location == LocationType.FRIDGE)
    item_to_keep = next(i for i in product.items if i.location == LocationType.PANTRY)

    # 2. Act: Remove the Fridge item
    updated_product = await testing_container.stock_service.remove_item(
        user_id, home_id, product.id, item_to_remove.id
    )

    # 3. Assert
    assert updated_product is not None
    assert updated_product.total_quantity == 3  # Only 3 left
    assert len(updated_product.items) == 1      # Only 1 item left
    assert updated_product.items[0].id == item_to_keep.id # Verify the correct one remained

    # Verify Persistence
    from_db = await testing_container.stock_repo.get_by_id(product.id)
    assert from_db.total_quantity == 3


@pytest.mark.asyncio
async def test_remove_item_full_deletion():
    """
    Scenario: Product has only 1 item. We remove it.
    Expected: Product is completely DELETED from DB (Cleanup).
    """
    user_id, home_id = await setup_env()

    # 1. Add product (1 Item)
    product = await testing_container.stock_service.add_product(
        "Milk", user_id, home_id, 5, "111", None, LocationType.FRIDGE, None
    )
    item_id = product.items[0].id

    # 2. Act: Remove the only item
    result = await testing_container.stock_service.remove_item(
        user_id, home_id, product.id, item_id
    )

    # 3. Assert
    assert result is None # Service returns None on deletion
    
    # Verify DB is empty
    products_in_db = await testing_container.stock_repo.list_all_by_home(home_id)
    assert len(products_in_db) == 0


@pytest.mark.asyncio
async def test_remove_item_fails_invalid_id():
    """
    Scenario: Trying to remove an item ID that doesn't exist in the product.
    Expected: ValueError.
    """
    user_id, home_id = await setup_env()

    product = await testing_container.stock_service.add_product(
        "Milk", user_id, home_id, 5, "111", None, LocationType.FRIDGE, None
    )
    
    fake_item_id = uuid4()

    with pytest.raises(ValueError, match="not found"): # Matching message from Product entity
        await testing_container.stock_service.remove_item(
            user_id, home_id, product.id, fake_item_id
        )


@pytest.mark.asyncio
async def test_update_item_quantity_success():
    """
    Scenario: User edits the quantity of a specific batch (e.g., from 12 to 6).
    Expected: Quantity updates in memory and DB.
    """
    user_id, home_id = await setup_env()
    
    # 1. Add product with 12 items
    product = await testing_container.stock_service.add_product(
        "Eggs", user_id, home_id, 12, "123", None, LocationType.FRIDGE, None
    )
    item_id = product.items[0].id
    
    # 2. Act: Update quantity to 6
    updated_product = await testing_container.stock_service.update_item_quantity(
        user_id, home_id, product.id, item_id, 6
    )
    
    # 3. Assert
    assert updated_product.items[0].quantity == 6
    assert updated_product.total_quantity == 6
    
    # Verify Persistence
    from_db = await testing_container.stock_repo.get_by_id(product.id)
    assert from_db.items[0].quantity == 6


@pytest.mark.asyncio
async def test_update_item_quantity_to_zero_removes_item():
    """
    Scenario: Product has 2 items. Update one of them to quantity 0.
    Expected: That specific item is removed, Product remains with the other item.
    """
    user_id, home_id = await setup_env()
    
    # 1. Setup: Add 2 items (Fridge and Pantry)
    product = await testing_container.stock_service.add_product(
        "Milk", user_id, home_id, 5, "111", None, LocationType.FRIDGE, None
    )
    product = await testing_container.stock_service.add_product(
        "Milk", user_id, home_id, 3, "111", None, LocationType.PANTRY, None
    )
    
    # Identify the Fridge item
    item_fridge = next(i for i in product.items if i.location == LocationType.FRIDGE)
    
    # 2. Act: Update Fridge item to 0
    updated_product = await testing_container.stock_service.update_item_quantity(
        user_id, home_id, product.id, item_fridge.id, 0
    )
    
    # 3. Assert
    assert updated_product is not None
    assert updated_product.total_quantity == 3 # Only Pantry quantity remains
    assert len(updated_product.items) == 1     # Only 1 item left in list
    
    # Verify the correct item remains
    assert updated_product.items[0].location == LocationType.PANTRY


@pytest.mark.asyncio
async def test_update_item_quantity_to_zero_deletes_product_if_last():
    """
    Scenario: Product has 1 item. Update it to 0.
    Expected: The Item is removed -> Product becomes empty -> Product is deleted.
    """
    user_id, home_id = await setup_env()
    
    # 1. Setup: 1 Item
    product = await testing_container.stock_service.add_product(
        "Milk", user_id, home_id, 5, "111", None, LocationType.FRIDGE, None
    )
    item_id = product.items[0].id
    
    # 2. Act: Update to 0
    result = await testing_container.stock_service.update_item_quantity(
        user_id, home_id, product.id, item_id, 0
    )
    
    # 3. Assert
    assert result is None # Service returns None when product is deleted
    
    # Verify DB is empty (Product gone)
    products_in_db = await testing_container.stock_repo.list_all_by_home(home_id)
    assert len(products_in_db) == 0


@pytest.mark.asyncio
async def test_update_item_quantity_fails_negative():
    """
    Scenario: User tries to set a negative quantity.
    Expected: ValueError (from Domain).
    """
    user_id, home_id = await setup_env()
    
    # 1. Add product
    product = await testing_container.stock_service.add_product(
        "Eggs", user_id, home_id, 12, "123", None, LocationType.FRIDGE, None
    )
    item_id = product.items[0].id
    
    # 2. Act & Assert
    # Note: We match "cannot be negative" because that's what we wrote in the Product entity
    with pytest.raises(ValueError, match="cannot be negative"):
        await testing_container.stock_service.update_item_quantity(
            user_id, home_id, product.id, item_id, -5
        )


@pytest.mark.asyncio
async def test_update_item_quantity_fails_invalid_item_id():
    """
    Scenario: User tries to update an item ID that does not exist.
    Expected: ValueError.
    """
    user_id, home_id = await setup_env()
    
    product = await testing_container.stock_service.add_product(
        "Eggs", user_id, home_id, 12, "123", None, LocationType.FRIDGE, None
    )
    
    fake_id = uuid4()
    
    with pytest.raises(ValueError, match="not found"):
        await testing_container.stock_service.update_item_quantity(
            user_id, home_id, product.id, fake_id, 5
        )

@pytest.mark.asyncio
async def test_update_item_date_simple_change():
    """
    Scenario: User changes expiration date from Jan 1 to Feb 1.
    No other items exist, so it's a simple field update.
    """
    user_id, home_id = await setup_env()
    old_date = date(2025, 1, 1)
    new_date = date(2025, 2, 1)
    
    # 1. Add product
    product = await testing_container.stock_service.add_product(
        "Cheese", user_id, home_id, 1, "123", old_date, LocationType.FRIDGE, None
    )
    item_id = product.items[0].id
    
    # 2. Act: Update Date
    updated_product = await testing_container.stock_service.update_item_date(
        user_id, home_id, product.id, item_id, new_date
    )
    
    # 3. Assert
    assert len(updated_product.items) == 1
    assert updated_product.items[0].expiration_date == new_date
    
    # Verify DB
    from_db = await testing_container.stock_repo.get_by_id(product.id)
    assert from_db.items[0].expiration_date == new_date


@pytest.mark.asyncio
async def test_update_item_date_merges_duplicates():
    """
    Scenario: 
    Batch A: Expire Jan 1 (Qty 2)
    Batch B: Expire Feb 1 (Qty 3)
    User changes Batch B date to Jan 1.
    Expected: Batches merge -> One batch, Jan 1, Qty 5.
    """
    user_id, home_id = await setup_env()
    date_1 = date(2025, 1, 1)
    date_2 = date(2025, 2, 1)
    
    # 1. Setup: Two batches in same location
    product = await testing_container.stock_service.add_product(
        "Yogurt", user_id, home_id, 2, "111", date_1, LocationType.FRIDGE, None
    )
    product = await testing_container.stock_service.add_product(
        "Yogurt", user_id, home_id, 3, "111", date_2, LocationType.FRIDGE, None
    )
    
    assert len(product.items) == 2
    
    # Identify the item with date_2 (to be changed)
    item_to_change = next(i for i in product.items if i.expiration_date == date_2)
    
    # 2. Act: Change date_2 -> date_1
    updated_product = await testing_container.stock_service.update_item_date(
        user_id, home_id, product.id, item_to_change.id, date_1
    )
    
    # 3. Assert
    assert len(updated_product.items) == 1 # Merged into one
    
    merged_item = updated_product.items[0]
    assert merged_item.expiration_date == date_1
    assert merged_item.quantity == 5 # 2 + 3
    
    # Verify DB
    from_db = await testing_container.stock_repo.get_by_id(product.id)
    assert len(from_db.items) == 1
    assert from_db.total_quantity == 5

@pytest.mark.asyncio
async def test_update_item_location_success():
    """
    Scenario: Move an item from PANTRY to FRIDGE.
    Expected: Location updates in memory and DB.
    """
    user_id, home_id = await setup_env()
    
    # 1. Add product to PANTRY
    product = await testing_container.stock_service.add_product(
        "Tuna", user_id, home_id, 2, "111", None, LocationType.PANTRY, None
    )
    item_id = product.items[0].id
    
    # 2. Act: Move to FRIDGE
    updated_product = await testing_container.stock_service.update_item_location(
        user_id, home_id, product.id, item_id, LocationType.FRIDGE
    )
    
    # 3. Assert
    assert len(updated_product.items) == 1
    assert updated_product.items[0].location == LocationType.FRIDGE
    
    # Verify Persistence
    from_db = await testing_container.stock_repo.get_by_id(product.id)
    assert from_db.items[0].location == LocationType.FRIDGE


@pytest.mark.asyncio
async def test_update_item_location_fails_invalid_item_id():
    """
    Scenario: Try to update location for an item ID that doesn't exist.
    Expected: ValueError.
    """
    user_id, home_id = await setup_env()
    
    product = await testing_container.stock_service.add_product(
        "Tuna", user_id, home_id, 2, "111", None, LocationType.PANTRY, None
    )
    
    fake_item_id = uuid4()
    
    with pytest.raises(ValueError, match="not found"):
        await testing_container.stock_service.update_item_location(
            user_id, home_id, product.id, fake_item_id, LocationType.FRIDGE
        )


@pytest.mark.asyncio
async def test_update_item_location_merges_duplicates():
    """
    Scenario: 
    - Item A: Cola in FRIDGE (Qty 2)
    - Item B: Cola in PANTRY (Qty 3)
    Action: Move Item B to FRIDGE.
    Expected: Since they share the same expiration date (None), 
              they should MERGE into one FRIDGE item with Qty 5.
    """
    user_id, home_id = await setup_env()
    
    # 1. Add Item A (Fridge)
    product = await testing_container.stock_service.add_product(
        "Cola", user_id, home_id, 2, "111", None, LocationType.FRIDGE, None
    )
    # Add Item B (Pantry) - Adds to the same product entity
    product = await testing_container.stock_service.add_product(
        "Cola", user_id, home_id, 3, "111", None, LocationType.PANTRY, None
    )
    
    assert len(product.items) == 2
    item_pantry = next(i for i in product.items if i.location == LocationType.PANTRY)
    
    # 2. Act: Move Pantry item to Fridge
    updated_product = await testing_container.stock_service.update_item_location(
        user_id, home_id, product.id, item_pantry.id, LocationType.FRIDGE
    )
    
    # 3. Assert
    # Expectation: Items merged! Only 1 item remains.
    assert len(updated_product.items) == 1
    
    merged_item = updated_product.items[0]
    assert merged_item.location == LocationType.FRIDGE
    assert merged_item.quantity == 5 # 2 + 3


@pytest.mark.asyncio
async def test_update_nickname_success():
    """
    Scenario: User updates nickname from None to 'My Milk'.
    Expected: Nickname updates, Original name remains 'Milk'.
    """
    user_id, home_id = await setup_env()
    
    # 1. Add product (Original name: "Milk")
    product = await testing_container.stock_service.add_product(
        "Milk", user_id, home_id, 1, "111", None, LocationType.FRIDGE, None
    )
    
    # 2. Act: Update Nickname
    updated_product = await testing_container.stock_service.update_nickname(
        user_id, home_id, product.id, "My Milk"
    )
    
    # 3. Assert
    assert updated_product.nickname == "My Milk"
    assert updated_product.original_name == "Milk" # Should verify original name is untouched
    
    # Verify DB
    from_db = await testing_container.stock_repo.get_by_id(product.id)
    assert from_db.nickname == "My Milk"


@pytest.mark.asyncio
async def test_update_nickname_overwrites_existing():
    """
    Scenario: Changing an existing nickname to a new one.
    """
    user_id, home_id = await setup_env()
    
    # 1. Add product with initial nickname
    product = await testing_container.stock_service.add_product(
        "Milk", user_id, home_id, 1, "111", None, LocationType.FRIDGE, "Old Nick"
    )
    
    # 2. Act
    updated_product = await testing_container.stock_service.update_nickname(
        user_id, home_id, product.id, "New Nick"
    )
    
    # 3. Assert
    assert updated_product.nickname == "New Nick"


# ==========================================
# 1. Location Filtering Tests
# ==========================================

@pytest.mark.asyncio
async def test_filter_by_location_partial_view():
    """
    Scenario: Product exists in FRIDGE (Qty 3) and PANTRY (Qty 2).
    Action: Filter by FRIDGE.
    Expected: 
    - Return ProductDTO with total_quantity=3 (not 5).
    - Contains only 1 item (the Fridge one).
    """
    user_id, home_id = await setup_env()
    
    # 1. Setup Data
    # Add Fridge Item
    product = await testing_container.stock_service.add_product(
        "Milk", user_id, home_id, 3, "111", None, LocationType.FRIDGE, None
    )
    # Add Pantry Item (Same product name -> Merges into same Product entity)
    await testing_container.stock_service.add_product(
        "Milk", user_id, home_id, 2, "111", None, LocationType.PANTRY, None
    )

    # 2. Act
    results = await testing_container.stock_service.filter_by_location(
        user_id, home_id, LocationType.FRIDGE
    )

    # 3. Assert
    assert len(results) == 1
    dto = results[0]
    
    # Verify strict filtering
    assert dto.total_quantity == 3          # Should ignore the pantry quantity
    assert len(dto.items) == 1
    assert dto.items[0].location == LocationType.FRIDGE
    
    # Verify DTO Structure
    assert dto.original_name == "Milk"
    assert dto.id == product.id


@pytest.mark.asyncio
async def test_filter_by_location_no_matches():
    """
    Scenario: Product exists only in FRIDGE.
    Action: Filter by FREEZER.
    Expected: Empty list (Product should not be returned at all).
    """
    user_id, home_id = await setup_env()
    
    await testing_container.stock_service.add_product(
        "Ice Cream", user_id, home_id, 1, "222", None, LocationType.FRIDGE, None
    )

    results = await testing_container.stock_service.filter_by_location(
        user_id, home_id, LocationType.FREEZER
    )

    assert len(results) == 0


# ==========================================
# 2. Expiration Filtering Tests
# ==========================================

@pytest.mark.asyncio
async def test_filter_by_expiration_fresh_only():
    """
    Scenario: 
    - Batch A: FRESH (Future Date)
    - Batch B: EXPIRED (Past Date)
    Action: Filter by FRESH.
    Expected: Only Batch A returned.
    """
    user_id, home_id = await setup_env()
    today = date.today()
    future_date = today + timedelta(days=30)
    past_date = today - timedelta(days=5)

    # Add Fresh Item
    await testing_container.stock_service.add_product(
        "Cheese", user_id, home_id, 5, "333", future_date, LocationType.FRIDGE, None
    )
    # Add Expired Item
    await testing_container.stock_service.add_product(
        "Cheese", user_id, home_id, 2, "333", past_date, LocationType.FRIDGE, None
    )

    # Act
    results = await testing_container.stock_service.filter_by_expiration_type(
        user_id, home_id, ExpirationType.FRESH
    )

    # Assert
    assert len(results) == 1
    dto = results[0]
    
    assert dto.total_quantity == 5  # Only the fresh ones
    assert len(dto.items) == 1
    assert dto.items[0].expiration_date == future_date
    assert dto.items[0].status == ExpirationType.FRESH


@pytest.mark.asyncio
async def test_filter_by_expiration_warning_status():
    """
    Scenario: Item expires in 2 days. Warning threshold is 3 days.
    Action: Filter by GOING_TO_EXPIRE.
    Expected: Item should be found and status calculated correctly.
    """
    user_id, home_id = await setup_env()
    
    # 2 days from now (Inside the 3-day warning window)
    warning_date = date.today() + timedelta(days=2) 
    
    await testing_container.stock_service.add_product(
        "Hummus", user_id, home_id, 1, "444", warning_date, LocationType.FRIDGE, None
    )

    # Act
    results = await testing_container.stock_service.filter_by_expiration_type(
        user_id, home_id, ExpirationType.GOING_TO_EXPIRE
    )

    # Assert
    assert len(results) == 1
    item_dto = results[0].items[0]
    
    assert item_dto.status == ExpirationType.GOING_TO_EXPIRE
    assert item_dto.expiration_date == warning_date


@pytest.mark.asyncio
async def test_filter_by_expiration_includes_no_date_as_fresh():
    """
    Scenario: Item has no expiration date (None).
    Action: Filter by FRESH.
    Expected: Should be included (None counts as Fresh).
    """
    user_id, home_id = await setup_env()
    
    await testing_container.stock_service.add_product(
        "Canned Beans", user_id, home_id, 10, "555", None, LocationType.PANTRY, None
    )

    results = await testing_container.stock_service.filter_by_expiration_type(
        user_id, home_id, ExpirationType.FRESH
    )

    assert len(results) == 1
    assert results[0].items[0].status == ExpirationType.FRESH


@pytest.mark.asyncio
async def test_search_product_by_name_success():
    """
    Scenario: User searches for 'Milk'. 
    Expected: Returns a list of Product entities containing 'Milk' in original_name.
    """
    user_id, home_id = await setup_env()
    
    # 1. Add Product
    await testing_container.stock_service.add_product(
        "Tnuva Milk 3%", user_id, home_id, 3, "111", None, LocationType.FRIDGE, None
    )

    # 2. Act
    results = await testing_container.stock_service.search_product(user_id, home_id, "Milk")

    # 3. Assert
    assert len(results) == 1
    product = results[0]
    
    # Verify we got the Domain Entity back
    assert isinstance(product, Product)
    assert product.original_name == "Tnuva Milk 3%"
    assert product.total_quantity == 3


@pytest.mark.asyncio
async def test_search_product_by_nickname_success():
    """
    Scenario: Product name is 'Cola', but nickname is 'My Morning Drink'.
    User searches for 'Morning'.
    Expected: Found via nickname.
    """
    user_id, home_id = await setup_env()
    
    await testing_container.stock_service.add_product(
        "Coca Cola", user_id, home_id, 1, "222", None, LocationType.FRIDGE, "My Morning Drink"
    )

    # Act
    results = await testing_container.stock_service.search_product(user_id, home_id, "Morning")

    # Assert
    assert len(results) == 1
    assert results[0].nickname == "My Morning Drink"


@pytest.mark.asyncio
async def test_search_product_case_insensitive():
    """
    Scenario: Product is 'Pasta'. User searches 'pasta' (lowercase).
    Expected: Match found.
    """
    user_id, home_id = await setup_env()
    
    await testing_container.stock_service.add_product(
        "Pasta", user_id, home_id, 5, "333", None, LocationType.PANTRY, None
    )

    # Act
    results = await testing_container.stock_service.search_product(user_id, home_id, "pasta")

    assert len(results) == 1
    assert results[0].original_name == "Pasta"


@pytest.mark.asyncio
async def test_search_product_returns_empty_list_when_no_match():
    """
    Scenario: Search for a term that doesn't exist.
    Expected: Empty list (not None).
    """
    user_id, home_id = await setup_env()
    
    await testing_container.stock_service.add_product(
        "Bread", user_id, home_id, 1, "444", None, LocationType.PANTRY, None
    )

    # Act
    results = await testing_container.stock_service.search_product(user_id, home_id, "Steak")

    # Assert
    assert isinstance(results, list)
    assert len(results) == 0


# ==========================================
# 3. External Provider & General Getters
# ==========================================

@pytest.mark.asyncio
async def test_search_product_by_name_external_db_success():
    """
    Scenario: Search in external DB by name.
    Expected: Calls provider and returns list of items.
    """
    user_id, home_id = await setup_env()
    
    # 1. Setup Mock Return Value
    # We use a simple object or MagicMock to represent the existing CatalogItem
    mock_item = MagicMock() 
    mock_item.name = "Bamba"
    mock_item.barcode = "9001"
    
    # Configure AsyncMock because the service method is async
    testing_container.stock_service._catalog_provider.search_items_by_name = AsyncMock(return_value=[mock_item])

    # 2. Act
    results = await testing_container.stock_service.search_product_by_name_external_db(
        user_id, home_id, "Bamba"
    )

    # 3. Assert
    assert len(results) == 1
    assert results[0].name == "Bamba"
    
    # Verify the provider was called correctly
    testing_container.stock_service._catalog_provider.search_items_by_name.assert_called_once_with("Bamba")


@pytest.mark.asyncio
async def test_search_product_by_barcode_external_db_success():
    """
    Scenario: Search in external DB by barcode.
    Expected: Calls provider and returns a single item.
    """
    user_id, home_id = await setup_env()
    
    # 1. Setup Mock Return Value
    mock_item = MagicMock()
    mock_item.name = "Milk"
    mock_item.barcode = "123456"
    
    testing_container.stock_service._catalog_provider.get_item_by_barcode = AsyncMock(return_value=mock_item)

    # 2. Act
    result = await testing_container.stock_service.search_product_by_barcode_external_db(
        user_id, home_id, "123456"
    )

    # 3. Assert
    assert result is not None
    assert result.name == "Milk"
    assert result.barcode == "123456"
    
    testing_container.stock_service._catalog_provider.get_item_by_barcode.assert_called_once_with("123456")


@pytest.mark.asyncio
async def test_search_product_by_barcode_external_db_not_found():
    """
    Scenario: Barcode not found in external DB.
    Expected: Returns None.
    """
    user_id, home_id = await setup_env()
    
    # Setup Mock to return None
    testing_container.stock_service._catalog_provider.get_item_by_barcode = AsyncMock(return_value=None)

    # Act
    result = await testing_container.stock_service.search_product_by_barcode_external_db(
        user_id, home_id, "999999"
    )

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_home_products_success():
    """
    Scenario: Retrieve all products in the home (Internal DB).
    """
    user_id, home_id = await setup_env()
    
    # 1. Setup: Add items to internal DB
    await testing_container.stock_service.add_product(
        "Milk", user_id, home_id, 1, "111", None, LocationType.FRIDGE, None
    )
    await testing_container.stock_service.add_product(
        "Bread", user_id, home_id, 1, "222", None, LocationType.PANTRY, None
    )

    # 2. Act
    products = await testing_container.stock_service.get_home_products(user_id, home_id)

    # 3. Assert
    assert len(products) == 2
    
    # Verify names
    names = [p.original_name for p in products]
    assert "Milk" in names
    assert "Bread" in names
    
    # Verify return type is List[Product]
    assert isinstance(products[0], Product)



import pytest
from datetime import date
from uuid import uuid4
from src.domain.receipt.receipt import ReceiptDTO, ReceiptItemDTO
from src.domain.enums import LocationType
from tests1.container import testing_container

@pytest.mark.asyncio
async def test_add_receipt_success():
    """
    Scenario: Process a receipt with multiple items.
    Expected: All items are added to the inventory, and the correct count is returned.
    """
    # 1. Setup environment
    user_id, home_id = await setup_env() # Helper from your existing test suite
    service = testing_container.stock_service
    
    # 2. Create ReceiptDTO
    items = [
        ReceiptItemDTO(
            name="Milk",
            quantity=2.0,
            barcode="111",
            expiration_date=date.today(),
            location=LocationType.FRIDGE
        ),
        ReceiptItemDTO(
            name="Bread",
            quantity=1.0,
            barcode="222",
            expiration_date=None,
            location=LocationType.PANTRY
        )
    ]
    
    receipt_dto = ReceiptDTO(
        id=uuid4(),
        home_id=home_id,
        user_id=user_id,
        items=items
    )
    
    # 3. Act
    added_count = await service.add_receipt(receipt_dto)
    
    # 4. Assert
    assert added_count == 2
    
    # Verify persistence via repository
    products = await testing_container.stock_repo.list_all_by_home(home_id)
    assert len(products) == 2
    
    names = {p.original_name for p in products}
    assert "Milk" in names
    assert "Bread" in names

@pytest.mark.asyncio
async def test_add_receipt_merges_with_existing_inventory():
    """
    Scenario: Receipt contains an item that already exists in the fridge.
    Expected: The quantities are merged into the existing product.
    """
    user_id, home_id = await setup_env()
    service = testing_container.stock_service

    # 1. Pre-add an item to inventory
    # Explicitly passing all required positional arguments to avoid TypeError
    await service.add_product(
        name="Butter",
        user_id=user_id,
        home_id=home_id,
        quantity=1,
        barcode="",           
        expiration_date=None,   
        location=LocationType.FRIDGE,
        nickname=None           
    )
    
    # 2. Add same item via receipt
    receipt_dto = ReceiptDTO(
        id=uuid4(),
        home_id=home_id,
        user_id=user_id,
        items=[
            ReceiptItemDTO(
                name="Butter",
                quantity=3.0,
                barcode="", # Fix: Must be a string
                location=LocationType.FRIDGE
            )
        ]
    )
    
    # Act: add_receipt uses add_product internally which handles the merge logic
    await service.add_receipt(receipt_dto)
    
    # Assert
    products = await testing_container.stock_repo.list_all_by_home(home_id)
    assert len(products) == 1 # Product aggregate remains the same
    assert products[0].total_quantity == 4 # Quantity is summed