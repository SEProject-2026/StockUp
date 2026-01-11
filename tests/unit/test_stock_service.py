import pytest
from uuid import UUID
from datetime import date, timedelta
from tests.container import testing_container
from src.domain.smart_home.enums import LocationType, ExpirationType

# --- Helper Functions ---

def setup_function():
    """
    Reset state before every test.
    """
    testing_container.reset_state()

async def setup_env():
    """
    Creates environment for Service Testing.
    CRITICAL LESSON FROM ROUTES: 
    We must manually convert Strings to Domain Objects (UUID) because 
    FastAPI isn't here to do it for us.
    """
    # 1. Register User
    # UserService returns a User Entity -> user.id is ALREADY a UUID object.
    user = await testing_container.user_service.register(
        "stock_test@test.com", "Pass123!", "Pass123!", "Stock User"
    )
    
    # 2. Create Home
    # ManagementService returns a Response DTO (Dict) -> id is a STRING.
    home = await testing_container.management_service.create_home(user.id, "My Stock Home")
    
    
    return user.id,home.get_id()   

# --- Tests ---

@pytest.mark.asyncio
async def test_add_product_success():
    user_id, home_id = await setup_env()
    
    # Act: Calling service directly requires correct types (UUID, int, date - NOT strings)
    await testing_container.stock_service.add_product(
        name="Milk",
        user_id=user_id,     # UUID
        home_id=home_id,     # UUID
        quantity=5,          # int
        barcode="729000",
        expiration_date=None, 
        location=None,
        nickname="My Snack"
    )
    
    # Assert: Verify Data in Repo
    products = await testing_container.stock_repo.list_all_by_home(home_id)
    assert len(products) == 1
    
    saved_product = products[0]
    assert saved_product.get_quantity() == 5
    assert saved_product.get_nickname() == "My Snack"
    assert saved_product.get_original_name() == "Milk"

@pytest.mark.asyncio
async def test_add_product_fails_if_home_not_found():
    user_id, _ = await setup_env()
    # Create a random UUID object (not string!)
    fake_home_id = UUID("00000000-0000-0000-0000-000000000000")
    
    with pytest.raises(ValueError, match="Home retrieval failed"):
        await testing_container.stock_service.add_product(
            "Milk", user_id, fake_home_id, 1, "123", None, None, None
        )

@pytest.mark.asyncio
async def test_add_product_fails_on_negative_quantity():
    user_id, home_id = await setup_env()
    
    with pytest.raises(ValueError, match="Quantity cannot be negative"):
        await testing_container.stock_service.add_product(
            "Milk", user_id, home_id, -1, "123", None, None, None
        )

@pytest.mark.asyncio
async def test_add_same_product_accumulates_quantity():
    user_id, home_id = await setup_env()
    barcode = "111"
    
    # 1. Add 3
    await testing_container.stock_service.add_product(
        "Product", user_id, home_id, 3, barcode, None, None, None
    )
    # 2. Add 3 more (same)
    await testing_container.stock_service.add_product(
        "Product", user_id, home_id, 3, barcode, None, None, None
    )
    
    # 3. Add 3 with DATE (Must use date object, not string!)
    future_date = date.today() + timedelta(days=5)
    await testing_container.stock_service.add_product(
        "Product", user_id, home_id, 3, barcode, future_date, None, None
    )

    products = await testing_container.stock_repo.list_all_by_home(home_id)
    assert len(products) == 1
    
    prod = products[0]
    assert prod.get_quantity() == 9
    assert len(prod.get_expiration_dates()) == 2

@pytest.mark.asyncio
async def test_remove_product_success():
    user_id, home_id = await setup_env()
    today = date.today()
    
    # Setup
    added_prod = await testing_container.stock_service.add_product(
        "Milk", user_id, home_id, 1, "123", today, None, None
    )
    
    # Act
    await testing_container.stock_service.remove_product(
        user_id, home_id, added_prod.get_id(), today
    )
    
    # Assert
    products = await testing_container.stock_repo.list_all_by_home(home_id)
    assert len(products) == 0

@pytest.mark.asyncio
async def test_update_quantity_success():
    user_id, home_id = await setup_env()
    today = date.today()
    
    product = await testing_container.stock_service.add_product(
        "Eggs", user_id, home_id, 12, "123", today, None, None
    )
    
    await testing_container.stock_service.update_date_quantity(
        user_id, home_id, product.get_id(), today, 5
    )
    
    updated = await testing_container.stock_repo.get_by_id(product.get_id())
    assert updated.get_quantity() == 5

@pytest.mark.asyncio
async def test_update_expiration_date():
    user_id, home_id = await setup_env()
    old_date = date.today() + timedelta(days=5)
    new_date = date.today() + timedelta(days=10)
    
    product = await testing_container.stock_service.add_product(
        "Cheese", user_id, home_id, 1, "123", old_date, None, None
    )
    
    await testing_container.stock_service.update_expiration_date(
        user_id, home_id, product.get_id(), old_date, new_date
    )
    
    updated = await testing_container.stock_repo.get_by_id(product.get_id())
    dates_map = updated.get_expiration_dates()
    
    assert new_date in dates_map
    assert old_date not in dates_map

@pytest.mark.asyncio
async def test_filter_by_expiration_type():
    user_id, home_id = await setup_env()
    expired_date = date.today() - timedelta(days=10)
    valid_date = date.today() + timedelta(days=10)
    
    await testing_container.stock_service.add_product(
        "Old Milk", user_id, home_id, 2, "111", expired_date, None, None
    )
    await testing_container.stock_service.add_product(
        "New Milk", user_id, home_id, 2, "222", valid_date, None, None
    )
    
    results = await testing_container.stock_service.filter_by_expiration_type(
        user_id, home_id, ExpirationType.EXPIRED
    )
    
    assert len(results) == 1
    assert results[0].original_name == "Old Milk"

@pytest.mark.asyncio
async def test_search_product():
    user_id, home_id = await setup_env()
    
    await testing_container.stock_service.add_product(
        "Coca Cola", user_id, home_id, 1, None, None, None, None
    )
    await testing_container.stock_service.add_product(
        "Pepsi", user_id, home_id, 1, None, None, None, None
    )
    
    results = await testing_container.stock_service.search_product(user_id, home_id, "Cola")
    
    assert len(results) == 1
    assert results[0].get_original_name() == "Coca Cola"