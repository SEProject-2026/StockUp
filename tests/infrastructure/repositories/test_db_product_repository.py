import pytest
from datetime import date, timedelta
from uuid import uuid4
from tests.container import testing_container
from src.domain.smart_home.product import Product
from src.domain.smart_home.enums import LocationType, ExpirationType
from src.domain.smart_home.home import Home
from src.domain.user import User

# --- Setup Hooks ---
def setup_module():
    testing_container.activate_db_mode()

def setup_function():
    testing_container.reset_state()

def teardown_module():
    testing_container.activate_memory_mode()

# --- Helpers ---

async def create_context():
    """
    Creates a User and a Home directly via Repositories.
    Returns Domain Objects: (User, Home)
    """
    # 1. Create & Save User
    user = User(email="stock_admin@test.com", hashed_password="pw", name="Stock Admin")
    await testing_container.user_repo.save(user)
    
    # 2. Create & Save Home (Linked to User)
    home = Home(user_id=user.id, name="Stock Home Repo")
    await testing_container.home_repo.save(home)
    
    return user, home

# --- Tests ---

@pytest.mark.asyncio
async def test_save_and_get_product():
    """
    Verifies saving a product with items (expiration dates) and retrieving it.
    """
    repo = testing_container.stock_repo
    user, home = await create_context()
    
    today = date.today()
    
    # 1. Create Product Domain Object
    product = (
        Product.builder(home.get_id(), "Milk", 2, 7)
        .with_expiration_date(today)
        .with_location(LocationType.FRIDGE)
        .build()
    )
    
    # 2. Save
    await repo.save(product)
    
    # 3. Retrieve
    fetched = await repo.get_by_id(product.get_id())
    
    # 4. Assert
    assert fetched is not None
    assert fetched.get_id() == product.get_id()
    assert fetched.get_original_name() == "Milk"
    assert fetched.get_quantity() == 2
    assert fetched.get_location() == LocationType.FRIDGE
    
    # Verify Items (Expiration Dates)
    dates_map = fetched.get_expiration_dates()
    assert today in dates_map
    assert dates_map[today][0] == 2 # Quantity

@pytest.mark.asyncio
async def test_update_product():
    """
    Verifies updating an existing product (changing quantity, nickname, location).
    """
    repo = testing_container.stock_repo
    _, home = await create_context()
    
    # 1. Save initial
    product = Product.builder(home.get_id(), "Eggs", 12, 7).build()
    await repo.save(product)
    
    # 2. Modify in memory
    product.set_nickname("Organic Eggs")
    product.set_location(LocationType.FRIDGE)
    
    # 3. Update
    await repo.update(product)
    
    # 4. Verify
    fetched = await repo.get_by_id(product.get_id())
    assert fetched.get_nickname() == "Organic Eggs"
    assert fetched.get_location() == LocationType.FRIDGE

@pytest.mark.asyncio
async def test_list_all_by_home():
    """
    Verifies fetching all products for a specific home.
    """
    repo = testing_container.stock_repo
    _, home = await create_context()
    
    # Add 2 products
    p1 = Product.builder(home.get_id(), "Apple", 5, 7).build()
    p2 = Product.builder(home.get_id(), "Banana", 3, 7).build()
    
    await repo.save(p1)
    await repo.save(p2)
    
    # Fetch
    products = await repo.list_all_by_home(home.get_id())
    
    assert len(products) == 2
    names = {p.get_original_name() for p in products}
    assert "Apple" in names
    assert "Banana" in names

@pytest.mark.asyncio
async def test_search_by_name_or_nickname():
    """
    Verifies partial search functionality.
    """
    repo = testing_container.stock_repo
    _, home = await create_context()
    
    # 1. "Coca Cola"
    p1 = Product.builder(home.get_id(), "Coca Cola", 1, 7).build()
    # 2. "Pepsi" with nickname "My Cola"
    p2 = Product.builder(home.get_id(), "Pepsi", 1, 7).with_nickname("My Cola").build()
    
    await repo.save(p1)
    await repo.save(p2)
    
    # Search "Cola" -> Should find both (one by name, one by nickname)
    results = await repo.search_by_name(home.get_id(), "Cola")
    
    assert len(results) == 2
    ids = {p.get_id() for p in results}
    assert p1.get_id() in ids
    assert p2.get_id() in ids

@pytest.mark.asyncio
async def test_get_by_location():
    """
    Verifies filtering by exact location string.
    """
    repo = testing_container.stock_repo
    _, home = await create_context()
    
    p1 = Product.builder(home.get_id(), "Ice", 1, 7).with_location(LocationType.FREEZER).build()
    p2 = Product.builder(home.get_id(), "Bread", 1, 7).with_location(LocationType.PANTRY).build()
    
    await repo.save(p1)
    await repo.save(p2)
    
    # Filter 'FREEZER' 
    # Note: DbProductRepository implementation expects the Enum name as string for the filter
    results = await repo.get_by_location(home.get_id(), "FREEZER")
    
    assert len(results) == 1
    assert results[0].get_original_name() == "Ice"

@pytest.mark.asyncio
async def test_delete_product():
    """
    Verifies deletion of a product.
    """
    repo = testing_container.stock_repo
    _, home = await create_context()
    
    p = Product.builder(home.get_id(), "Bad Apple", 1, 7).build()
    await repo.save(p)
    
    # Confirm exists
    assert await repo.get_by_id(p.get_id()) is not None
    
    # Delete
    await repo.delete(p.get_id())
    
    # Confirm gone
    assert await repo.get_by_id(p.get_id()) is None

@pytest.mark.asyncio
async def test_complex_item_persistence():
    """
    Verifies that multiple expiration dates for a single product are saved and loaded correctly.
    """
    repo = testing_container.stock_repo
    _, home = await create_context()
    
    date1 = date.today()
    date2 = date.today() + timedelta(days=10)
    
    # Create product
    p = Product.builder(home.get_id(), "MultiMilk", 0, 7).build()
    
    # Add items directly to internal state (simulating domain logic)
    p._expiration_dates_to_quantity[date1] = (5, ExpirationType.FRESH)
    p._expiration_dates_to_quantity[date2] = (3, ExpirationType.FRESH)
    p._expiration_dates_to_quantity.pop(None, None)
    p._quantity = 8
    
    await repo.save(p)
    
    # Fetch
    fetched = await repo.get_by_id(p.get_id())
    
    assert fetched.get_quantity() == 8
    dates = fetched.get_expiration_dates()
    assert len(dates) == 2
    assert dates[date1][0] == 5
    assert dates[date2][0] == 3