from uuid import UUID
from typing import List
from pydantic import BaseModel

class ShoppingListItem(BaseModel):
    item_name: str
    quantity: int

class ShoppingList(BaseModel):
    home_id: UUID
    is_active_shopping_mode: bool = False
    items: List[ShoppingListItem] = []

    def add_item(self, item_name: str, quantity: int) -> None:
        """Adds a new item or increments quantity if it exists."""
        pass

    def remove_item(self, item_name: str) -> None:
        """Removes the item from the list by its name."""
        pass

    def update_quantity(self, item_name: str, new_quantity: int) -> None:
        """Updates the quantity for a specific item name."""
        pass