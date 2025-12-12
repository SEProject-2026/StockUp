from datetime import date
from typing import Optional
from uuid import uuid4, UUID
from domain.smart_home.enums import ExpirationType, LocationType, ChainType

class Product:
    def __init__(self, 
                 home_id: UUID,
                 barcode: str,
                 name: str,
                 original_name: str,
                 quantity: int, 
                 location: Optional[LocationType], 
                 nickname: Optional[str] = None,
                 chain_origin: Optional[ChainType] = None,
                 expiration_date: Optional[date] = None):
        
        self._id = uuid4()
        self._home_id = home_id
        self._barcode = barcode
        self._name = name
        self._original_name = original_name
        self._nickname = nickname
        self._quantity = quantity
        self._location = location
        self._chain_origin = chain_origin
        self._expiration_type = ExpirationType.FRESH
        self._expiration_date = expiration_date

    # Getters
    def get_id(self) -> UUID:
        return self._id

    def get_home_id(self) -> UUID:
        return self._home_id

    def get_barcode(self) -> str:
        return self._barcode

    def get_name(self) -> str:
        return self._name

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
    
    def get_expiration_type(self) -> ExpirationType:
        return self._expiration_type

    def get_expiration_date(self) -> Optional[date]:
        return self._expiration_date 
    
    # Setters
    def set_nickname(self, new_nickname: str) -> None:
        self._nickname = new_nickname
        # Update display name accordingly
        self._name = new_nickname if new_nickname else self._original_name
    
    def set_expiration_date(self, new_date: date) -> None:
        self._expiration_date = new_date

    def set_expiration_type(self, new_expiration_type: ExpirationType) -> None:
        self._expiration_type = new_expiration_type
    
    def set_quantity(self, new_quantity: int) -> None:
        self._quantity = new_quantity

    def set_location(self, new_location: LocationType) -> None:
        self._location = new_location

    def to_dict(self) -> dict:
        return {
            "id": str(self._id),
            "home_id": str(self._home_id),
            "barcode": self._barcode,
            "name": self._name,
            "original_name": self._original_name,
            "nickname": self._nickname,
            "quantity": self._quantity,
            "location": self._location.name if self._location else None,
            "chain_origin": self._chain_origin.name if self._chain_origin else None,
            "expiration_type": self._expiration_type.name,
            "expiration_date": self._expiration_date.isoformat() if self._expiration_date else None
        }