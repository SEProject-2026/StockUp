from typing import List
from pydantic import BaseModel
from uuid import UUID

class BaseModeItem(BaseModel):
    item_name: str
    required_quantity: int

class BaseMode(BaseModel):
    home_id: UUID
    items: List[BaseModeItem] = []

    def add_item(self, item_name: str, quantity: int) -> None:
        """Adds a new requirement or updates quantity if name exists."""
        pass

    def remove_item(self, item_name: str) -> None:
        """Removes a requirement from the base mode configuration."""
        pass

    def update_quantity(self, item_name: str, new_quantity: int) -> None:
        """Updates the required quantity for an existing item."""
        pass