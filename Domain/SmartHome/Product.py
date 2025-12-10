from datetime import date
from enum import Enum, auto
from typing import Optional
from uuid import uuid4, UUID
from Domain.SmartHome.Enums import ExpirationType, LocationType


class Product:
    def __init__(self, barcode: str, name: str, nickname: str, quantity: int, location: LocationType, expiration_date: Optional[date] = None):
        self._id = uuid4()
        self._barcode = barcode
        self._name = name
        self._nickname = nickname
        self._quantity = quantity
        self._location = location
        self._expiration_type = ExpirationType.FRESH
        self._expiration_date = expiration_date

    def get_id(self) -> str:
        return self._id

    def get_name(self) -> str:
        return self._name

    def get_nickname(self) -> str:
        return self._nickname

    def get_quantity(self) -> int:
        return self._quantity
    
    def get_location(self) -> LocationType:
        return self._location
    
    def get_expiration_type(self) -> ExpirationType:
        return self._expiration_type

    def get_expiration_date(self) -> Optional[date]:
        return self._expiration_date 
    
    def set_nickname(self, new_nickname: str) -> None:
        self._nickname = new_nickname
    
    def set_expiration_date(self, new_date) -> None:
        self._expiration_date = new_date

    def set_expiration_type(self, new_expiration_type: ExpirationType) -> None:
        self._expiration_type = new_expiration_type
    
    def set_quantity(self, new_quantity: int) -> None:
        self._quantity = new_quantity

    def set_location(self, new_location: LocationType) -> None:
        self._location = new_location

    
    

    