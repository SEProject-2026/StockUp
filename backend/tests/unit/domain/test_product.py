import pytest
import uuid
from datetime import date, timedelta
from src.domain.enums import LocationType, ExpirationType
from src.domain.product.product import ProductItem

class TestProductDomain:

    # ==========================================
    # 1. ProductItem Logic (The inner entity)
    # ==========================================
    
    def test_product_item_status_calculation(self):
        """Happy Path: Verify status transitions based on warning_days threshold."""
        today = date.today()
        
        # Case: No expiration date -> FRESH
        assert ProductItem(expiration_date=None).get_status(3) == ExpirationType.FRESH
        
        # Case: Future date beyond threshold -> FRESH
        future_date = today + timedelta(days=10)
        assert ProductItem(expiration_date=future_date).get_status(3) == ExpirationType.FRESH
        
        # Case: Exactly on threshold boundary -> GOING_TO_EXPIRE
        threshold_date = today + timedelta(days=3)
        assert ProductItem(expiration_date=threshold_date).get_status(3) == ExpirationType.GOING_TO_EXPIRE
        
        # Case: Past date -> EXPIRED
        past_date = today - timedelta(days=1)
        assert ProductItem(expiration_date=past_date).get_status(3) == ExpirationType.EXPIRED

    # ==========================================
    # 2. Product Initialization & Basic Guards
    # ==========================================

    def test_product_initialization(self, any_product, any_home):
        """Happy Path: Verify product is linked to home and starts empty."""
        assert any_product.home_id == any_home._id
        assert any_product.total_quantity == 0
        assert len(any_product.items) == 0

    def test_add_item_with_defaults(self, any_product):
        """Happy Path: Providing None as location defaults to OTHER."""
        any_product.add_item(quantity=5, location=None)
        
        assert any_product.items[0].location == LocationType.OTHER
        assert any_product.total_quantity == 5

    def test_add_item_validation_fails(self, any_product):
        """Sad Path: Verify that adding zero or negative quantity raises ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            any_product.add_item(quantity=0)
        with pytest.raises(ValueError, match="must be positive"):
            any_product.add_item(quantity=-5)

    # ==========================================
    # 3. Removal & Quantity Updates
    # ==========================================

    def test_remove_item_success(self, any_product):
        """Happy Path: Manual removal of a batch."""
        any_product.add_item(quantity=10)
        item_id = any_product.items[0].id
        
        any_product.remove_item(item_id)
        assert len(any_product.items) == 0

    def test_remove_non_existent_item_fails(self, any_product):
        """Sad Path: Error when removing an ID that doesn't exist."""
        with pytest.raises(ValueError, match="not found"):
            any_product.remove_item(uuid.uuid4())

    def test_update_item_quantity_success(self, any_product):
        """Happy Path: Updating to a new positive quantity."""
        any_product.add_item(quantity=10)
        item_id = any_product.items[0].id
        
        any_product.update_item_quantity(item_id, 25)
        assert any_product.items[0].quantity == 25
        assert any_product.total_quantity == 25

    def test_update_quantity_to_zero_removes_item(self, any_product):
        """Happy Path: Domain rule - updating quantity to 0 removes the item line."""
        any_product.add_item(quantity=10)
        item_id = any_product.items[0].id
        
        any_product.update_item_quantity(item_id, 0)
        assert len(any_product.items) == 0

    def test_update_quantity_negative_fails(self, any_product):
        """Sad Path: Validation for negative quantity updates."""
        any_product.add_item(quantity=10)
        item_id = any_product.items[0].id
        
        with pytest.raises(ValueError, match="cannot be negative"):
            any_product.update_item_quantity(item_id, -1)

    # ==========================================
    # 4. Location & Date Merge Logic (Complex)
    # ==========================================

    def test_update_location_no_merge(self, any_product):
        """Happy Path: Moving an item to a new location preserves identity if unique."""
        any_product.add_item(quantity=5, location=LocationType.FRIDGE)
        item_id = any_product.items[0].id
        
        any_product.update_item_location(item_id, LocationType.PANTRY)
        
        assert any_product.items[0].location == LocationType.PANTRY
        assert any_product.items[0].id == item_id # Identity preserved

    def test_update_location_with_merge(self, any_product):
        """Happy Path: Moving item merges it into existing batch at target location."""
        expiry = date.today()
        any_product.add_item(quantity=2, location=LocationType.FRIDGE, expiration_date=expiry)
        any_product.add_item(quantity=3, location=LocationType.PANTRY, expiration_date=expiry)
        
        target_id = next(i.id for i in any_product.items if i.location == LocationType.FRIDGE)
        source_id = next(i.id for i in any_product.items if i.location == LocationType.PANTRY)
        
        # Act: Move pantry (3) to fridge (2)
        any_product.update_item_location(source_id, LocationType.FRIDGE)
        
        assert len(any_product.items) == 1
        assert any_product.total_quantity == 5
        assert any_product.items[0].id == target_id # Verify target swallowed the source

    def test_update_date_with_merge(self, any_product):
        """Happy Path: Changing date merges it into batch with same date/location."""
        date_a = date(2025, 1, 1)
        date_b = date(2025, 2, 1)
        
        any_product.add_item(quantity=10, location=LocationType.FRIDGE, expiration_date=date_a)
        any_product.add_item(quantity=5, location=LocationType.FRIDGE, expiration_date=date_b)
        
        target_id = next(i.id for i in any_product.items if i.expiration_date == date_a)
        source_id = next(i.id for i in any_product.items if i.expiration_date == date_b)
        
        # Act: Change Feb 1 to Jan 1
        any_product.update_item_date(source_id, date_a)
        
        assert len(any_product.items) == 1
        assert any_product.total_quantity == 15
        assert any_product.items[0].id == target_id

    def test_update_date_to_same_no_op(self, any_product):
        """Happy Path: Updating to the same date should not change anything."""
        expiry = date.today()
        any_product.add_item(quantity=5, expiration_date=expiry)
        item_id = any_product.items[0].id
        
        any_product.update_item_date(item_id, expiry)
        assert any_product.items[0].expiration_date == expiry
        assert len(any_product.items) == 1