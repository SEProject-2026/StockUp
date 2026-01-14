from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from src.domain.smart_home.enums import UnitType


class ReceiptItemDTO(BaseModel):
    """
    Represents a single line item extracted from a receipt.
    """
    barcode: str = Field(..., description="The barcode of the product")
    name: str = Field(..., description="The product name as extracted or matched")
    quantity: float = Field(..., gt=0, description="Quantity amount (must be positive)")
    unit: UnitType = Field(default=UnitType.UNIT, description="Unit of measurement")
    storage_category: Optional[str] = Field(default=None, description="Suggested storage category from catalog (fridge/freezer/pantry/cleaning/other)")

    model_config = ConfigDict(from_attributes=True)


class ReceiptDTO(BaseModel):
    """
    Represents a full receipt record as stored in the database.
    Includes metadata (ID, store, date) and the list of items.
    """
    id: UUID = Field(..., description="Unique identifier of the receipt")
    home_id: UUID = Field(..., description="The home ID this receipt belongs to")
    user_id: UUID = Field(..., description="The user who uploaded/created the receipt")
    
    chain: Optional[str] = Field(None, description="Name of the store (e.g. 'Rami Levi')")
    
    items: List[ReceiptItemDTO] = Field(default=[], description="List of items extracted from the receipt")

    model_config = ConfigDict(from_attributes=True)