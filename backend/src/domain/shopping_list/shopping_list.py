from uuid import UUID
from typing import List
from pydantic import BaseModel

class ShoppingListItem(BaseModel):
    item_name: str
    quantity: int
    is_bought: bool = False

class ShoppingList(BaseModel):
    home_id: UUID
    is_active_shopping_mode: bool = False
    items: List[ShoppingListItem] = []

    def add_item(self, item_name: str, quantity: int) -> None:
        for item in self.items:
            if item.item_name == item_name:
                item.quantity += quantity
                return
        self.items.append(ShoppingListItem(item_name=item_name, quantity=quantity))

    def remove_item(self, item_name: str) -> None:
        for i, item in enumerate(self.items):
            if item.item_name == item_name:
                del self.items[i]
                return

    def update_quantity(self, item_name: str, new_quantity: int) -> None:
        """Updates the quantity for a specific item name."""
        for item in self.items:
            if item.item_name == item_name:
                item.quantity = new_quantity
                return
    
    def enter_shopping_mode(self) -> None:
        self.is_active_shopping_mode = True

    def check_item_as_bought(self, item_name: str) -> None:
        for item in self.items:
            if item.item_name == item_name:
                item.is_bought = True
                return

    def exit_shopping_mode(self) -> None:
        self.is_active_shopping_mode = False
        for i, item in enumerate(self.items):
            if item.is_bought or item.quantity == 0:
                del self.items[i]
                return
                