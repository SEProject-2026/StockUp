from __future__ import annotations
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import date
from dataclasses import dataclass, field
from src.domain.smart_home.enums import LocationType, ExpirationType

@dataclass
class ProductItem:
    """
    Represents a specific batch/line in the inventory.
    """
    id: UUID = field(default_factory=uuid4)
    quantity: int = 0
    expiration_date: Optional[date] = None
    location: LocationType = LocationType.OTHER

    def get_status(self, warning_days: int) -> ExpirationType:
        """
        Calculates status dynamically based on home settings.
        :param warning_days: The threshold defined by the home configuration (e.g., 3 days).
        """
        if self.expiration_date is None:
            return ExpirationType.FRESH 

        today = date.today()
        delta = (self.expiration_date - today).days

        if delta < 0:
            return ExpirationType.EXPIRED
        elif 0 <= delta <= warning_days:
            return ExpirationType.GOING_TO_EXPIRE
        else:
            return ExpirationType.FRESH

class Product:
    def __init__(
        self, 
        id: UUID, 
        home_id: UUID, 
        original_name: str,
        barcode: Optional[str] = None,
        nickname: Optional[str] = None
    ):
        self.id = id
        self.home_id = home_id
        self.original_name = original_name
        self.barcode = barcode
        self.nickname = nickname
        
        # Internal storage
        self._items: List[ProductItem] = []

    # ==========================================
    # Properties
    # ==========================================

    @property
    def items(self) -> List[ProductItem]:
        """Returns a copy of the list to prevent external modification."""
        return list(self._items)

    @property
    def total_quantity(self) -> int:
        """Calculates total stock across all batches."""
        return sum(item.quantity for item in self._items)

    # ==========================================
    # Domain Actions
    # ==========================================

    def set_nickname(self, new_nickname: str) -> None:
        self.nickname = new_nickname

    def add_item(self, quantity: int, location: Optional[LocationType] = None, expiration_date: Optional[date] = None) -> None:
        """
        Smart Add:
        If location is None, defaults to LocationType.OTHER.
        """
        if quantity <= 0:
            raise ValueError("Quantity to add must be positive")

        # Resolve default location inside the domain
        effective_location = location if location else LocationType.OTHER

        # 1. Try to merge with existing batch using effective_location
        for item in self._items:
            if item.location == effective_location and item.expiration_date == expiration_date:
                item.quantity += quantity
                return

        # 2. Create new batch
        new_item = ProductItem(
            quantity=quantity,
            expiration_date=expiration_date,
            location=effective_location # Guaranteed to be a real Enum, not None
        )
        self._items.append(new_item)

    def remove_item(self, item_id: UUID) -> None:
        """Completely removes a specific line item."""
        for i, item in enumerate(self._items):
            if item.id == item_id:
                self._items.pop(i)
                return
        
        raise ValueError(f"Item {item_id} not found in product {self.id}")

    def update_item_quantity(self, item_id: UUID, new_quantity: int) -> None:
        """
        Updates quantity for specific ID.
        Smart Logic: 
        - If new_quantity is 0 -> Removes the item.
        - If new_quantity < 0 -> Raises Error.
        """
        if new_quantity < 0:
            raise ValueError("Quantity cannot be negative")

        if new_quantity == 0:
            # Domain logic: 0 means "remove this line"
            self.remove_item(item_id)
            return

        # Regular update
        for item in self._items:
            if item.id == item_id:
                item.quantity = new_quantity
                return
        
        raise ValueError(f"Item {item_id} not found")

    # ==========================================
    # Update Methods with Merge Logic
    # ==========================================

    def update_item_location(self, item_id: UUID, new_location: LocationType) -> None:
        """
        Updates the location of a specific item.
        If an item with the same expiration_date already exists in the new_location,
        it merges them (adds quantity to the target and removes the source).
        """
        # 1. Find the item to move
        item_to_move = next((i for i in self._items if i.id == item_id), None)
        if not item_to_move:
            raise ValueError(f"Item {item_id} not found")

        # Optimization: If location hasn't changed, do nothing
        if item_to_move.location == new_location:
            return

        # 2. Check for merge target (Same location, Same date, Different ID)
        target_item = next((
            i for i in self._items 
            if i.location == new_location 
            and i.expiration_date == item_to_move.expiration_date
            and i.id != item_id
        ), None)

        if target_item:
            # Merge Logic: Add quantity to target, remove source
            target_item.quantity += item_to_move.quantity
            self._items.remove(item_to_move)
        else:
            # Update Logic: Just change location
            item_to_move.location = new_location

    def update_item_date(self, item_id: UUID, new_date: Optional[date]) -> None:
        """
        Updates expiration date.
        If changing date creates a duplicate (same location + new date already exists),
        it merges the quantities and deletes the old item ID.
        """
        # 1. Find the source item
        source_item = self._get_item_by_id(item_id)
        
        if source_item.expiration_date == new_date:
            return 

        # 2. Check for merge conflict
        target_item = self._find_merge_candidate(
            exclude_id=item_id,
            location=source_item.location,
            expiration_date=new_date
        )

        if target_item:
            # Merge source into target
            target_item.quantity += source_item.quantity
            self._items.remove(source_item)
        else:
            # Just update
            source_item.expiration_date = new_date

    # ==========================================
    # Private Helpers
    # ==========================================

    def _get_item_by_id(self, item_id: UUID) -> ProductItem:
        for item in self._items:
            if item.id == item_id:
                return item
        raise ValueError(f"Item {item_id} not found")

    def _find_merge_candidate(self, exclude_id: UUID, location: LocationType, expiration_date: Optional[date]) -> Optional[ProductItem]:
        """
        Looks for ANOTHER item that matches the location/date criteria to allow merging.
        """
        for item in self._items:
            if item.id != exclude_id and item.location == location and item.expiration_date == expiration_date:
                return item
        return None