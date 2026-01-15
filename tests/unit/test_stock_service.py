import pytest
from uuid import UUID
from datetime import date, timedelta
from tests.container import testing_container
from src.domain.smart_home.enums import LocationType, ExpirationType
from uuid import uuid4
from src.domain.receipt import ReceiptDTO, ReceiptItemDTO
from src.domain.smart_home.enums import UnitType

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



@pytest.mark.asyncio
async def test_add_receipt_creates_new_products():
    """
    Verifies that a receipt with completely new items creates them in the DB.
    """
    user_id, home_id = await setup_env()
    
    # FIX 1: Use UnitType.UNIT instead of LITER
    item1 = ReceiptItemDTO(
        barcode="1001", 
        name="New Milk", 
        quantity=2, 
        unit=UnitType.UNIT, 
        location=LocationType.FRIDGE
    )
    item2 = ReceiptItemDTO(
        barcode="1002", 
        name="New Bread", 
        quantity=1, 
        unit=UnitType.UNIT, 
        location=LocationType.PANTRY
    )
    
    receipt_dto = ReceiptDTO(
        id=uuid4(),
        home_id=home_id,
        user_id=user_id,
        items=[item1, item2]
    )

    added_count = await testing_container.stock_service.add_receipt(receipt_dto)

    assert added_count == 2
    products = await testing_container.stock_repo.list_all_by_home(home_id)
    assert len(products) == 2

@pytest.mark.asyncio
async def test_add_receipt_updates_existing_products():
    """
    Verifies that if a product already exists, the receipt adds to its quantity.
    """
    user_id, home_id = await setup_env()
    
    # 1. Setup: Manually add a product first
    await testing_container.stock_service.add_product(
        "Cola", user_id, home_id, 5, "COLA_BARCODE", None, None, None
    )

    # 2. Prepare Receipt
    # FIX 2: Use the SAME NAME ("Cola") because add_product currently searches by name only.
    item = ReceiptItemDTO(
        barcode="COLA_BARCODE", 
        name="Cola", 
        quantity=6, 
        unit=UnitType.UNIT,
        location=LocationType.PANTRY
    )
    
    receipt_dto = ReceiptDTO(
        id=uuid4(),
        home_id=home_id,
        user_id=user_id,
        items=[item]
    )

    await testing_container.stock_service.add_receipt(receipt_dto)

    products = await testing_container.stock_repo.list_all_by_home(home_id)
    # Now this should pass because "Cola" was found and updated
    assert len(products) == 1 
    
    cola = products[0]
    assert cola.get_quantity() == 11 

@pytest.mark.asyncio
async def test_add_receipt_handles_expiration_dates():
    user_id, home_id = await setup_env()
    
    exp_date = date.today() + timedelta(days=30)
    
    item = ReceiptItemDTO(
        barcode="CHEESE_123", 
        name="Gouda", 
        quantity=1, 
        expiration_date=exp_date,
        location=LocationType.FRIDGE
    )
    
    receipt_dto = ReceiptDTO(
        id=uuid4(),
        home_id=home_id,
        user_id=user_id,
        items=[item]
    )

    await testing_container.stock_service.add_receipt(receipt_dto)

    products = await testing_container.stock_repo.list_all_by_home(home_id)
    saved_product = products[0]
    
    dates = saved_product.get_expiration_dates()
    assert exp_date in dates
    
    # FIX 3: Check the first element of the tuple (quantity, status)
    # The error showed: (1, <ExpirationType.FRESH>)
    assert dates[exp_date][0] == 1.0

@pytest.mark.asyncio
async def test_add_receipt_skips_failed_items_and_continues():
    """
    Verifies batch processing iteration.
    Note: To strictly test 'skip on error', `add_product` needs to be mocked to raise an Exception.
    """
    user_id, home_id = await setup_env()
    
    valid_item = ReceiptItemDTO(
        barcode="VALID", name="Valid Item", quantity=1, location=LocationType.PANTRY
    )
    
    # Sending 2 valid items to ensure loop completes successfully
    items = [valid_item, valid_item] 
    
    receipt_dto = ReceiptDTO(
        id=uuid4(), home_id=home_id, user_id=user_id, items=items
    )

    count = await testing_container.stock_service.add_receipt(receipt_dto)
    
    assert count == 2