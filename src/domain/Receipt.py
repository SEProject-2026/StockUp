from datetime import date
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from src.domain.smart_home.enums import LocationType, UnitType


class ReceiptItemDTO(BaseModel):
    """
    Represents a single line item extracted from a receipt.
    """
    # Change from str to Optional[str] to allow None in tests/scans
    name: str = Field(..., min_length=2, description="The product name")
    # Change to Optional if you want to allow None, or keep str if using ""
    barcode: Optional[str] = Field(None, description="The barcode of the product")
    quantity: float = Field(..., gt=0, description="Quantity amount (must be positive)")
    unit: UnitType = Field(default=UnitType.UNIT, description="Unit of measurement")
    location: Optional[LocationType] = Field(default=LocationType.OTHER, description="Suggested storage location")
    expiration_date: Optional[date]= Field(None, description="Expiration date if available/applicable")
    nickname: Optional[str] = Field(None, description="Optional nickname for the product")

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