from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from src.domain.enums import LocationType

# --- Response DTOs ---

class ShoppingListItemDTO(BaseModel):
    """Data Transfer Object for individual items within a list."""
    model_config = ConfigDict(from_attributes=True)
    item_name: str
    quantity: int
    is_bought: bool
    location: Optional[LocationType] = LocationType.OTHER



class ShoppingListDTO(BaseModel):
    """Main Data Transfer Object for Shopping List responses."""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    home_id: UUID
    name: str
    is_active_shopping_mode: bool
    items: List[ShoppingListItemDTO]
    updated_at: datetime


# --- Request Schemas ---

class CreateShoppingListRequest(BaseModel):
    """Payload for creating a new list."""
    home_id: UUID
    name: str = Field(..., min_length=1, max_length=100)


class AddItemRequest(BaseModel):
    """Payload for adding an item to a list."""
    item_name: str = Field(..., min_length=1)
    quantity: int = Field(..., gt=0)
    location: Optional[LocationType] = LocationType.OTHER


class UpdateQuantityRequest(BaseModel):
    """Payload for updating item quantity."""
    new_quantity: int = Field(..., ge=0)


class ExitModeRequest(BaseModel):
    """Payload for exiting shopping mode."""
    clear: bool = Field(default=False)