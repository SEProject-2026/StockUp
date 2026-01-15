from pydantic import BaseModel, Field
from uuid import UUID
from typing import List, Optional, Dict, Any
from datetime import date
from src.domain.receipt import ReceiptItemDTO
from src.domain.smart_home.enums import LocationType, ExpirationType


class ProductItemDTO(BaseModel):
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
    quantity: int
    items: List[ProductItemDTO] = []

    @classmethod
    def from_domain(cls, product: Any) -> "ProductDTO":
        domain_items = product.get_expiration_dates() 
        parsed_items = []
        
        if domain_items:
            for exp_date, (qty, status) in domain_items.items():
                parsed_items.append(ProductItemDTO(
                    expiration_date=exp_date,
                    quantity=qty,
                    status=status
                ))
            
            parsed_items.sort(key=lambda x: x.expiration_date or date.max)

        return cls(
            id=product.get_id(),
            home_id=product.get_home_id(),
            original_name=product.get_original_name(),
            nickname=product.get_nickname(),
            barcode=product.get_barcode(),
            location=product.get_location(),
            quantity=product.get_quantity(),
            items=parsed_items
        )

class AddProductRequest(BaseModel):
    name: str
    quantity: int
    expiration_date: Optional[date] = None
    barcode: Optional[str] = None
    location: Optional[LocationType] = LocationType.OTHER
    nickname: Optional[str] = None

class UpdateProductQuantityRequest(BaseModel):
    expiration_date: Optional[date]
    new_quantity: int

class UpdateExpirationDateRequest(BaseModel):
    old_date: Optional[date]
    new_date: Optional[date]

class UpdateProductNicknameRequest(BaseModel):
    nickname: str


class AddReceiptRequest(BaseModel):
    """
    Body payload for submitting the final verified receipt items.
    """
    home_id: UUID = Field(..., description="The home ID to add items to")
    chain: Optional[str] = Field(None, description="The name of the store/chain (e.g. Rami Levi)")
    items: List[ReceiptItemDTO] = Field(..., description="List of verified items to add")