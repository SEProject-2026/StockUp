import pytest
from uuid import uuid4
from datetime import date, timedelta
from src.domain.product.product import Product, ProductItem
from src.domain.enums import LocationType, ExpirationType

# ==========================================
# Fixtures
# ==========================================

@pytest.fixture
def empty_product():
    return Product(
        id=uuid4(),
        home_id=uuid4(),
        original_name="Test Product",
        barcode="123456",
        nickname="Nick"
    )

# ==========================================
# 1. Product Item Status Tests
# ==========================================

def test_product_item_status_fresh():
    """Verifies status is FRESH when expiration is far in the future."""
    future_date = date.today() + timedelta(days=10)
    item = ProductItem(expiration_date=future_date)
    
    # Threshold is 3 days, item expires in 10
    status = item.get_status(warning_days=3)
    assert status == ExpirationType.FRESH

def test_product_item_status_going_to_expire():
    """Verifies status is GOING_TO_EXPIRE when within the warning threshold."""
    near_future_date = date.today() + timedelta(days=2)
    item = ProductItem(expiration_date=near_future_date)
    
    # Threshold is 3 days, item expires in 2
    status = item.get_status(warning_days=3)
    assert status == ExpirationType.GOING_TO_EXPIRE

def test_product_item_status_expired():
    """Verifies status is EXPIRED when date is in the past."""
    past_date = date.today() - timedelta(days=1)
    item = ProductItem(expiration_date=past_date)
    
    status = item.get_status(warning_days=3)
    assert status == ExpirationType.EXPIRED

def test_product_item_status_no_date():
    """Verifies status is FRESH (or Valid) if no expiration date exists."""
    item = ProductItem(expiration_date=None)
    status = item.get_status(warning_days=3)
    assert status == ExpirationType.FRESH

# ==========================================
# 2. Add / Remove / Quantity Logic
# ==========================================

def test_add_item_creates_new_batch(empty_product):
    """Adding an item with unique properties should create a new entry."""
    empty_product.add_item(5, LocationType.FRIDGE, date(2025, 1, 1))
    
    assert len(empty_product.items) == 1
    assert empty_product.total_quantity == 5
    assert empty_product.items[0].location == LocationType.FRIDGE

def test_add_item_merges_existing_batch(empty_product):
    """Adding an item with SAME location and date should merge into existing entry."""
    target_date = date(2025, 1, 1)
    
    # 1. Add initial batch
    empty_product.add_item(5, LocationType.FRIDGE, target_date)
    
    # 2. Add more to same batch
    empty_product.add_item(3, LocationType.FRIDGE, target_date)
    
    assert len(empty_product.items) == 1
    assert empty_product.total_quantity == 8
    assert empty_product.items[0].quantity == 8

def test_add_item_handles_none_location(empty_product):
    """If location is None, it should default to OTHER."""
    empty_product.add_item(2, location=None)
    
    assert empty_product.items[0].location == LocationType.OTHER

def test_remove_item_success(empty_product):
    """Should successfully remove an item by ID."""
    empty_product.add_item(5, LocationType.FRIDGE)
    item_id = empty_product.items[0].id
    
    empty_product.remove_item(item_id)
    
    assert len(empty_product.items) == 0
    assert empty_product.total_quantity == 0

def test_remove_item_not_found(empty_product):
    """Should raise ValueError if trying to remove non-existent ID."""
    with pytest.raises(ValueError, match="not found"):
        empty_product.remove_item(uuid4())

def test_update_quantity_success(empty_product):
    """Should update absolute quantity."""
    empty_product.add_item(5, LocationType.FRIDGE)
    item_id = empty_product.items[0].id
    
    empty_product.update_item_quantity(item_id, 10)
    
    assert empty_product.items[0].quantity == 10

def test_update_quantity_negative_fails(empty_product):
    """Should prevent setting negative or zero quantity via update."""
    empty_product.add_item(5, LocationType.FRIDGE)
    item_id = empty_product.items[0].id
    
    with pytest.raises(ValueError, match="cannot be negative"):
        empty_product.update_item_quantity(item_id, -1)

def test_update_quantity_to_zero_removes_item(empty_product):
    """
    Scenario: Setting quantity to 0 via update should trigger removal.
    """
    empty_product.add_item(5, LocationType.FRIDGE)
    item_id = empty_product.items[0].id
    
    # Act: Update to 0
    empty_product.update_item_quantity(item_id, 0)
    
    # Assert: Item should be gone
    assert len(empty_product.items) == 0
    assert empty_product.total_quantity == 0

def test_update_quantity_negative_fails(empty_product):
    """Should prevent setting negative quantity."""
    empty_product.add_item(5, LocationType.FRIDGE)
    item_id = empty_product.items[0].id
    
    # Only strictly negative numbers throw error now
    with pytest.raises(ValueError, match="cannot be negative"):
        empty_product.update_item_quantity(item_id, -1)

# ==========================================
# 3. Merge Logic (Location & Date Updates)
# ==========================================

def test_update_location_simple_move(empty_product):
    """
    Scenario: Moving an item to a location where no matching batch exists.
    Expected: Only the location field updates. ID remains same.
    """
    empty_product.add_item(5, LocationType.FRIDGE, date(2025, 1, 1))
    item = empty_product.items[0]
    original_id = item.id
    
    empty_product.update_item_location(original_id, LocationType.PANTRY)
    
    assert len(empty_product.items) == 1
    updated_item = empty_product.items[0]
    assert updated_item.location == LocationType.PANTRY
    assert updated_item.id == original_id # ID preserved

def test_update_location_merges_duplicates(empty_product):
    """
    Scenario: 
    1. Batch A: Fridge, Date X, Qty 2
    2. Batch B: Pantry, Date X, Qty 3
    3. Move Batch B to Fridge.
    Expected: Batch B merges into Batch A. Total Qty 5. Batch B removed.
    """
    target_date = date(2025, 1, 1)
    
    # 1. Setup batches
    empty_product.add_item(2, LocationType.FRIDGE, target_date) # Target
    empty_product.add_item(3, LocationType.PANTRY, target_date) # Source (to be moved)
    
    items = empty_product.items
    target_item = next(i for i in items if i.location == LocationType.FRIDGE)
    source_item = next(i for i in items if i.location == LocationType.PANTRY)
    
    # 2. Perform Move (Pantry -> Fridge)
    empty_product.update_item_location(source_item.id, LocationType.FRIDGE)
    
    # 3. Assertions
    assert len(empty_product.items) == 1
    final_item = empty_product.items[0]
    
    assert final_item.location == LocationType.FRIDGE
    assert final_item.quantity == 5 # 2 + 3
    assert final_item.id == target_item.id # Should keep the target ID

def test_update_date_merges_duplicates(empty_product):
    """
    Scenario:
    1. Batch A: Fridge, Date Jan 1, Qty 2
    2. Batch B: Fridge, Date Feb 1, Qty 3
    3. Change Batch B date to Jan 1.
    Expected: Batch B merges into Batch A. Total Qty 5.
    """
    date_1 = date(2025, 1, 1)
    date_2 = date(2025, 2, 1)
    
    # 1. Setup batches (Same location, diff dates)
    empty_product.add_item(2, LocationType.FRIDGE, date_1)
    empty_product.add_item(3, LocationType.FRIDGE, date_2)
    
    items = empty_product.items
    target_item = next(i for i in items if i.expiration_date == date_1)
    source_item = next(i for i in items if i.expiration_date == date_2)
    
    # 2. Update Date (Feb 1 -> Jan 1)
    empty_product.update_item_date(source_item.id, date_1)
    
    # 3. Assertions
    assert len(empty_product.items) == 1
    final_item = empty_product.items[0]
    
    assert final_item.expiration_date == date_1
    assert final_item.quantity == 5 # 2 + 3