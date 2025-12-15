from datetime import date
from typing import Optional
from uuid import uuid4, UUID
from src.domain.smart_home.enums import ExpirationType, LocationType, ChainType
from src.domain.domain_exception import DomainException


class ProductBuilder:

    def __init__(self, home_id: UUID, barcode: str, name: str, quantity: int):
        self._home_id = home_id
        self._barcode = barcode
        self._original_name = name
        self._quantity = quantity
        self._nickname: Optional[str] = None
        self._location: Optional[LocationType] = None
        self._chain_origin: Optional[ChainType] = None
        self._expiration_date: Optional[date] = None

    def with_original_name(self, original_name: str) -> 'ProductBuilder':
        self._original_name = original_name
        return self

    def with_nickname(self, new_nickname: str) -> 'ProductBuilder':
        self._nickname = new_nickname
        return self

    def with_location(self, location: LocationType) -> 'ProductBuilder':
        if location:
            self._location = location
        return self

    def with_chain_origin(self, chain: ChainType) -> 'ProductBuilder':
        if chain:
            self._chain_origin = chain
        return self

    def with_expiration_date(self, exp_date: date) -> 'ProductBuilder':
        self._expiration_date = exp_date
        return self

    def build(self) -> 'Product':
        return Product(
            home_id=self._home_id,
            barcode=self._barcode,
            original_name=self._original_name,
            quantity=self._quantity,
            location=self._location,
            nickname=self._nickname,
            chain_origin=self._chain_origin,
            expiration_date=self._expiration_date
        )


class Product:

    def builder(home_id: UUID, barcode: str, name: str, quantity: int) -> 'ProductBuilder':
        return ProductBuilder(home_id, barcode, name, quantity)
    
    NICKNAME_MAX_LENGTH = 20

    def __init__(self, 
                 home_id: UUID,
                 barcode: str,
                 original_name: str,
                 quantity: int, 
                 location: Optional[LocationType], 
                 nickname: Optional[str] = None,
                 chain_origin: Optional[ChainType] = None,
                 expiration_date: Optional[date] = None):
        
        self._id = uuid4()
        self._home_id = home_id
        self._barcode = barcode
        self._original_name = original_name
        self.set_nickname(nickname)
        self.set_quantity(quantity)
        self._location = location
        self._chain_origin = chain_origin
        self.set_expiration_date(expiration_date)
        self._expiration_type = ExpirationType.FRESH

    # Getters
    def get_id(self) -> UUID:
        return self._id

    def get_home_id(self) -> UUID:
        return self._home_id

    def get_barcode(self) -> str:
        return self._barcode

    def get_original_name(self) -> str:
        return self._original_name

    def get_nickname(self) -> Optional[str]:
        return self._nickname

    def get_quantity(self) -> int:
        return self._quantity
    
    def get_location(self) -> Optional[LocationType]:
        return self._location
    
    def get_chain_origin(self) -> Optional[ChainType]:
        return self._chain_origin
    
    def get_expiration_type(self) -> Optional[ExpirationType]:
        return self._expiration_type

    def get_expiration_date(self) -> Optional[date]:
        return self._expiration_date 
    
    # Setters
    def set_nickname(self, new_nickname: str) -> None:
        if new_nickname is None:
            self._nickname = None
            return
        if self._is_valid_name(new_nickname):
            self._nickname = new_nickname    

    def set_expiration_date(self, new_date: date) -> None:
        if new_date is None:
            self._expiration_date = None
            return
        elif new_date < date.today():
            raise ValueError("Expiration date cannot be in the past.")          
        self._expiration_date = new_date

    def set_expiration_type(self, new_expiration_type: ExpirationType) -> None:
        self._expiration_type = new_expiration_type
    
    def set_quantity(self, new_quantity: int) -> None:
        if new_quantity < 0:
            raise DomainException("Quantity cannot be negative.")
        self._quantity = new_quantity

    def set_location(self, new_location: LocationType) -> None:
        self._location = new_location

    def _is_valid_name(self, new_nickname: str) -> bool:
        if new_nickname.strip() == "":
            raise ValueError("Nickname cannot be empty.")
        if len(new_nickname) > self.NICKNAME_MAX_LENGTH:
            raise ValueError(f"Nickname is too long (max {self.NICKNAME_MAX_LENGTH} chars).")
        if "  " in new_nickname:
            raise ValueError("Nickname cannot contain consecutive spaces.")
        clean_name = new_nickname.replace(" ", "")
        if not clean_name.isalnum():
            raise ValueError("Nickname must contain only letters or numbers.")
        return True

  
    def to_dict(self) -> dict:
        return {
            "id": str(self._id),
            "home_id": str(self._home_id),
            "barcode": self._barcode,
            "chain_origin": self._chain_origin.name if self._chain_origin else None,
            "original_name": self._original_name,
            "nickname": self._nickname,
            "quantity": self._quantity,
            "location": self._location.name if self._location else None,
            "expiration_type": self._expiration_type.name,
            "expiration_date": self._expiration_date.isoformat() if self._expiration_date else None
        }

         

