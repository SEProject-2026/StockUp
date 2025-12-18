from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date
from src.domain.smart_home.enums import LocationType, ExpirationType

# --------------------------------------
# Shared / Base Models
# --------------------------------------

class ProductItemDTO(BaseModel):
    """
    Represents a single entry of expiration date and quantity within a product.
    Example: 5 units expiring on 01/01/2025 with status FRESH.
    """
    expiration_date: Optional[date]
    quantity: int
    status: ExpirationType

class ProductDTO(BaseModel):
    id: UUID
    home_id: UUID
    original_name: str
    nickname: Optional[str] = None
    barcode: Optional[str] = None
    location: Optional[LocationType] = None
    total_quantity: int = Field(alias="quantity") # Maps to the domain's 'quantity' field
    items: List[ProductItemDTO] = [] # Flattened list of expiration dates

    model_config = ConfigDict(from_attributes=True)

    @field_validator("items", mode="before")
    @classmethod
    def parse_expiration_map(cls, v: Any) -> List[Dict]:
        """
        Critical function: Converts the domain's complex dictionary structure:
        {date: (qty, type)}
        Into a JSON-friendly flattened list:
        [{date: ..., qty: ..., status: ...}, ...]
        """
        if isinstance(v, dict):
            parsed_items = []
            for exp_date, (qty, status) in v.items():
                parsed_items.append({
                    "expiration_date": exp_date,
                    "quantity": qty,
                    "status": status
                })
            # Sort by date (soonest to expire first)
            parsed_items.sort(key=lambda x: x["expiration_date"] or date.max)
            return parsed_items
        return v

# --------------------------------------
# Input Models (Requests)
# --------------------------------------

class AddProductRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    quantity: int = Field(..., gt=0)
    barcode: Optional[str] = None
    nickname: Optional[str] = Field(None, max_length=20)
    location: Optional[LocationType] = LocationType.OTHER
    expiration_date: Optional[date] = None

class UpdateProductQuantityRequest(BaseModel):
    # Date is required to identify which specific batch to update
    expiration_date: Optional[date] = None 
    new_quantity: int = Field(..., ge=0)

class UpdateProductLocationRequest(BaseModel):
    location: LocationType

class UpdateProductNicknameRequest(BaseModel):
    nickname: str = Field(..., min_length=1, max_length=20)

class UpdateExpirationDateRequest(BaseModel):
    old_date: Optional[date]
    new_date: date