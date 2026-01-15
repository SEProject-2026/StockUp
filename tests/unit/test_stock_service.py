import pytest
from uuid import UUID, uuid4
from datetime import date, timedelta
from tests.container import testing_container
from src.domain.smart_home.enums import LocationType

# --- Helper Functions ---

def setup_function():
    """
    Reset state before every test.
    """
    testing_container.reset_state()

async def setup_env():
    """
    Creates environment for Service Testing.
    """
    # 1. Register User
    user = await testing_container.user_service.register(
        "stock_test@test.com", "Pass123!", "Pass123!", "Stock User"
    )
    
    # 2. Create Home
    home = await testing_container.management_service.create_home(user.id, "My Stock Home")
    
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