import pytest
from datetime import date, timedelta
from uuid import uuid4
from tests.container import testing_container
from src.domain.product.product import Product
from src.domain.enums import LocationType
from src.domain.home.home import Home
from src.domain.user.user import User

# --- Helpers ---

async def create_context():
    """
    Creates a User and a Home directly via Repositories.
    Returns Domain Objects: (User, Home)
    """
    # 1. Create & Save User
    user = User(email="stock_repo@test.com", hashed_password="pw", name="Repo User")
    await testing_container.user_repo.save(user)
    
    # 2. Create & Save Home (Linked to User)
    home = Home(user_id=user.id, name="Repo Home")
    await testing_container.home_repo.save(home)
    
    return user, home

# --- Tests ---

@pytest.mark.asyncio
async def test_save_and_get_product():
    """
    Verifies saving a product with items and retrieving it.
    """
    repo = testing_container.stock_repo
    user, home = await create_context()
    
    today = date.today()
    
    # 1. Create Product (Using Constructor, accessing .id directly)
    product = Product(
        id=uuid4(),
        home_id=home.get_id(),  # Changed from .get_id()
        original_name="Milk",
        barcode="123456",
        nickname=None
    )
    # Add Item
    product.add_item(quantity=2, location=LocationType.FRIDGE, expiration_date=today)
    
    # 2. Save
    await repo.save(product)
    
    # 3. Retrieve
    fetched = await repo.get_by_id(product.id) 
    
    # 4. Assert
    assert fetched is not None
    assert fetched.id == product.id
    assert fetched.original_name == "Milk"
    assert fetched.total_quantity == 2
    
    # Verify Items
    assert len(fetched.items) == 1
    fetched_item = fetched.items[0]
    assert fetched_item.quantity == 2
    assert fetched_item.location == LocationType.FRIDGE
    assert fetched_item.expiration_date == today


@pytest.mark.asyncio
async def test_update_product():
    """
    Verifies updating an existing product (changing nickname, adding items).
    """
    repo = testing_container.stock_repo
    _, home = await create_context()
    
    # 1. Save initial
    product = Product(uuid4(), home.get_id(), "Eggs", "999")
    product.add_item(12, LocationType.FRIDGE, None)
    await repo.save(product)
    
    # 2. Modify in memory
    product.set_nickname("Organic Eggs")
    
    # Change Item quantity via Product method
    item_id = product.items[0].id
    product.update_item_quantity(item_id, 6)
    
    # 3. Update in DB
    await repo.update(product)
    
    # 4. Verify
    fetched = await repo.get_by_id(product.id)
    assert fetched.nickname == "Organic Eggs"
    assert fetched.total_quantity == 6
    assert fetched.items[0].quantity == 6


@pytest.mark.asyncio
async def test_list_all_by_home():
    """
    Verifies fetching all products for a specific home.
    """
    repo = testing_container.stock_repo
    _, home = await create_context()
    
    # Add 2 products
    p1 = Product(uuid4(), home.get_id(), "Apple")
    p1.add_item(5, LocationType.FRIDGE, None)
    
    p2 = Product(uuid4(), home.get_id(), "Banana")
    p2.add_item(3, LocationType.PANTRY, None)
    
    await repo.save(p1)
    await repo.save(p2)
    
    # Fetch
    products = await repo.list_all_by_home(home.get_id())
    
    assert len(products) == 2
    names = {p.original_name for p in products}
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
    p1 = Product(uuid4(), home.get_id(), "Coca Cola")
    p1.add_item(1, LocationType.FRIDGE, None)
    
    # 2. "Pepsi" with nickname "My Cola"
    p2 = Product(uuid4(), home.get_id(), "Pepsi", nickname="My Cola")
    p2.add_item(1, LocationType.FRIDGE, None)
    
    await repo.save(p1)
    await repo.save(p2)
    
    # Search "Cola" -> Should find both (one by name, one by nickname)
    results = await repo.search_by_name(home.get_id(), "Cola")
    
    assert len(results) == 2
    ids = {p.id for p in results}
    assert p1.id in ids
    assert p2.id in ids


@pytest.mark.asyncio
async def test_delete_product():
    """
    Verifies deletion of a product.
    """
    repo = testing_container.stock_repo
    _, home = await create_context()
    
    p = Product(uuid4(), home.get_id(), "Bad Apple")
    p.add_item(1, LocationType.OTHER, None)
    await repo.save(p)
    
    # Confirm exists
    assert await repo.get_by_id(p.id) is not None
    
    # Delete
    await repo.delete(p.id)
    
    # Confirm gone
    assert await repo.get_by_id(p.id) is None


@pytest.mark.asyncio
async def test_complex_item_persistence():
    """
    Verifies that multiple items (batches) for a single product are saved and loaded correctly.
    """
    repo = testing_container.stock_repo
    _, home = await create_context()
    
    date1 = date.today()
    date2 = date.today() + timedelta(days=10)
    
    # Create product
    p = Product(uuid4(), home.get_id(), "MultiMilk")
    
    # Add multiple batches
    p.add_item(5, LocationType.FRIDGE, date1)
    p.add_item(3, LocationType.FRIDGE, date2)
    
    await repo.save(p)
    
    # Fetch
    fetched = await repo.get_by_id(p.id)
    
    assert fetched.total_quantity == 8 # 5 + 3
    assert len(fetched.items) == 2
    
    # Verify specific items exist
    q1 = next(i.quantity for i in fetched.items if i.expiration_date == date1)
    q2 = next(i.quantity for i in fetched.items if i.expiration_date == date2)
    
    assert q1 == 5
    assert q2 == 3