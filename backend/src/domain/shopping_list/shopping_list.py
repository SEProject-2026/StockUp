from datetime import datetime
from uuid import UUID, uuid4
from typing import List, Optional
from pydantic import BaseModel, Field


class ShoppingListItem(BaseModel):
    item_name: str
    quantity: int
    is_bought: bool = False
    location: str = "OTHER"

class ShoppingList(BaseModel):
    id: UUID= Field(default_factory=uuid4)
    name: str
    home_id: UUID
    is_active_shopping_mode: bool = False
    items: List[ShoppingListItem] = []
    updated_at: datetime = Field(default_factory=datetime.now)

    def _refresh_timestamp(self):
        self.updated_at = datetime.now()

    def add_item(self, item_name: str, quantity: int, location: str = "OTHER") -> None:
        for item in self.items:
            if item.item_name == item_name:
                item.quantity += quantity
                self._refresh_timestamp()
                return
        self.items.append(ShoppingListItem(item_name=item_name, quantity=quantity, location=location))
        self._refresh_timestamp()

    def remove_item(self, item_name: str) -> None:
        for i, item in enumerate(self.items):
            if item.item_name == item_name:
                del self.items[i]
                self._refresh_timestamp()
                return
        raise ValueError(f"Item not found: {item_name}")

    def update_quantity(self, item_name: str, new_quantity: int) -> None:
        """Updates the quantity for a specific item name."""
        for item in self.items:
            if item.item_name == item_name:
                item.quantity = new_quantity
                self._refresh_timestamp()
                return
        raise ValueError(f"Item not found: {item_name}")

    def enter_shopping_mode(self) -> None:
        self.is_active_shopping_mode = True

    def check_item_as_bought(self, item_name: str) -> None:
        for item in self.items:
            if item.item_name == item_name:
                item.is_bought = not item.is_bought  # Toggle bought status
                self._refresh_timestamp()
                return
        raise ValueError(f"Item not found: {item_name}")

    def exit_shopping_mode(self, clear: bool = False) -> None:
        """
        Deactivates shopping mode. 
        If clear is True, removes the items that were marked as bought.
        """
        self.is_active_shopping_mode = False
        
        if clear:
            self.items = [item for item in self.items if not item.is_bought]
            
        self._refresh_timestamp()
