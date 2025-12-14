from datetime import date
from typing import Optional
from uuid import UUID
from domain.smart_home.product import Product
from domain.smart_home.enums import LocationType, ChainType

class ProductBuilder:

    NICKNAME_MAX_LENGTH = 20

    def __init__(self, home_id: UUID, barcode: str, name: str, quantity: int):
        self._home_id = home_id
        self._barcode = barcode
        self._name = name
        if quantity < 0:
            raise ValueError("Quantity cannot be negative.")
        self._quantity = quantity
        self._original_name = name
        self._nickname: Optional[str] = None
        self._location: Optional[LocationType] = None
        self._chain_origin: Optional[ChainType] = None
        self._expiration_date: Optional[date] = None

    def with_original_name(self, original_name: str) -> ProductBuilder:
        if original_name:
            self._original_name = original_name
        return self

    def with_nickname(self, new_nickname: str) -> ProductBuilder:
        if not new_nickname or new_nickname.strip() == "":
            raise ValueError("Nickname cannot be empty.")
        if len(new_nickname) > self.NICKNAME_MAX_LENGTH:
            raise ValueError(f"Nickname is too long (max {self.NICKNAME_MAX_LENGTH} chars).")
        if not self._is_valid_name(new_nickname):
            raise ValueError("Nickname contains invalid characters.")
        self._nickname = new_nickname
        return self
    
    def _is_valid_name(self, new_nickname: str) -> bool:
        if "  " in new_nickname:
            return False
        clean_name = new_nickname.replace(" ", "")
        if not clean_name.isalnum():
            return False
        return True

    def with_location(self, location: LocationType) -> ProductBuilder:
        if location:
            self._location = location
        return self

    def with_chain_origin(self, chain: ChainType) -> ProductBuilder:
        if chain:
            self._chain_origin = chain
        return self

    def with_expiration_date(self, exp_date: date) -> ProductBuilder:
        if exp_date and exp_date > date.today():
            self._expiration_date = exp_date
        return self

    def build(self) -> Product:
        return Product(
            home_id=self._home_id,
            barcode=self._barcode,
            name=self._name,
            original_name=self._original_name,
            quantity=self._quantity,
            location=self._location,
            nickname=self._nickname,
            chain_origin=self._chain_origin,
            expiration_date=self._expiration_date
        )