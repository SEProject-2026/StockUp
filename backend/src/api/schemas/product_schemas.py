from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from typing import List, Optional, Any
from datetime import date
from src.domain.receipt import ReceiptItemDTO
from src.domain.smart_home.enums import LocationType, ExpirationType, UnitType

# ==========================================
# Response Models (DTOs)
# ==========================================

class ProductItemDTO(BaseModel):
    id: UUID
    quantity: float
    expiration_date: Optional[date]
    location: LocationType        
    status: ExpirationType        
    
    model_config = ConfigDict(from_attributes=True)

class ProductDTO(BaseModel):
    id: UUID
    home_id: UUID
    original_name: str
    nickname: Optional[str] = None
    barcode: Optional[str] = None
    
    total_quantity: float           
    items: List[ProductItemDTO] = []
    
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain(cls, product: Any) -> "ProductDTO":
        parsed_items = []
        
        # Iterating over the list of ProductItem entities
        for item in product.items:
            parsed_items.append(ProductItemDTO(
                id=item.id,
                quantity=item.quantity,
                expiration_date=item.expiration_date,
                location=item.location,
                # need to fix 
                status=item.get_status(7) 
            ))
            
        # Sort items by date (None/No-Date goes last)
        parsed_items.sort(key=lambda x: x.expiration_date or date.max)

        return cls(
            id=product.id,
            home_id=product.home_id,
            original_name=product.original_name,
            nickname=product.nickname,
            barcode=product.barcode,
            total_quantity=product.total_quantity,
            items=parsed_items
        )

# ==========================================
# Request Models (Inputs with Validation)
# ==========================================

class AddProductRequest(BaseModel):
    name: str = Field(
        ..., 
        min_length=2, 
        max_length=100, 
        description="Product name must be between 2 and 100 characters"
    )
    quantity: int = Field(
        ..., 
        gt=0, 
        description="Initial quantity must be greater than 0"
    )
    expiration_date: Optional[date] = None
    barcode: Optional[str] = Field(
        None, 
        max_length=50, 
        description="Barcode string"
    )
    location: Optional[LocationType] = LocationType.OTHER
    nickname: Optional[str] = Field(
        None, 
        min_length=2, 
        max_length=50, 
        description="Nickname must be between 2 and 50 characters"
    )

class UpdateItemQuantityRequest(BaseModel):
    new_quantity: int = Field(
        ..., 
        ge=0, 
        description="Quantity must be 0 or greater. Setting to 0 removes the item."
    )

class UpdateItemExpirationRequest(BaseModel):
    new_date: Optional[date] = Field(
        None, 
        description="New expiration date (or null to remove expiration)"
    )

class UpdateProductNicknameRequest(BaseModel):
    nickname: str = Field(
        ..., 
        min_length=2, 
        max_length=50, 
        description="New nickname cannot be empty"
    )

class UpdateItemLocationRequest(BaseModel):
    location: LocationType = Field(
        ..., 
        description="New location from the allowed enum values"
    )



class ReceiptItem(BaseModel):
    name: str = Field(..., min_length=2)
    quantity: float = Field(..., gt=0)
    barcode: Optional[str] = None
    expiration_date: Optional[date] = None
    location: LocationType = LocationType.OTHER
    unit:UnitType = UnitType.UNIT
    nickname: Optional[str] = None
    weight: Optional[float] = None
    

class AddReceiptRequest(BaseModel):
    chain:str
    items: List[ReceiptItem]
