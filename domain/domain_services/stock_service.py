from datetime import date
from typing import Dict, Optional
from uuid import uuid4, UUID
from domain import User
from domain.smart_home.enums import ChainType, LocationType, ExpirationType
from domain.smart_home.product import Product
from domain.smart_home.home import Home
from domain.domain_services.domain_exception import DomainException
from response import Response


class StockService:

    NICKNAME_MAX_LENGTH = 20

    def __init__(self):
        pass

    def create_home_product(self, 
                            home_id: UUID,
                            barcode: str,
                            product_name: str,
                            chain: ChainType,
                            quantity: int,
                            expiration_date: Optional[date],
                            location: Optional[str],
                            nickname: Optional[str]) -> Product:
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        
        final_display_name = nickname if nickname else product_name

        new_product = Product(
            id=uuid4(),
            home_id=home_id,
            barcode=barcode,
            name=final_display_name,
            original_name=product_name,
            quantity=quantity,
            expiration_date=expiration_date,
            location=location,
            chain_origin=chain
        )

        return new_product
    
    def update_quantity(self, product: Product, new_quantity: int) -> None:
        if new_quantity < 0:
            raise DomainException("Quantity cannot be negative.")
        product.set_quantity(new_quantity)
        
    
    def update_expiration_date(self, product: Product, new_date: date) -> None:
        if new_date < date.today():
            raise DomainException("Expiration date cannot be in the past.")
        product.set_expiration_date(new_date)
    
    def update_nickname(self, product: Product, new_nickname: str) -> None:
        if not new_nickname or new_nickname.strip() == "":
            raise ValueError("Nickname cannot be empty.")
        
        if len(new_nickname) > self.NICKNAME_MAX_LENGTH:
            raise ValueError(f"Nickname is too long (max {self.NICKNAME_MAX_LENGTH} chars).")
        
        if not self._is_valid_name(new_nickname):
            raise ValueError("Nickname contains invalid characters.")
        
        product.set_nickname(new_nickname)
    
    def is_valid_name(new_nickname: str) -> bool:
        if "  " in new_nickname:
            return False
        clean_name = new_nickname.replace(" ", "")
        if not clean_name.isalnum():
            return False
            
        return True