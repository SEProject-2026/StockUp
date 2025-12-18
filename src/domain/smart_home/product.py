from datetime import date
from typing import Optional
from uuid import uuid4, UUID
from src.domain.smart_home.enums import ExpirationType, LocationType


class ProductBuilder:

    def __init__(self, home_id: UUID, name: str, quantity: int, expiration_range: int):
        self._home_id = home_id
        self._original_name = name
        self._quantity = quantity
        self._expiration_range = expiration_range
        self._barcode: Optional[str] = None
        self._nickname: Optional[str] = None
        self._location: Optional[LocationType] = None
        self._expiration_date: Optional[date] = None

    def with_barcode(self, barcode: str) -> 'ProductBuilder':
        self._barcode = barcode
        return self

    def with_nickname(self, new_nickname: str) -> 'ProductBuilder':
        self._nickname = new_nickname
        return self

    def with_location(self, location: LocationType) -> 'ProductBuilder':
        if location:
            self._location = location
        return self

    def with_expiration_date(self, exp_date: date) -> 'ProductBuilder':
        self._expiration_date = exp_date
        return self
    
    def with_expiration_range(self, exp_range: int) -> 'ProductBuilder':
        self._expiration_range = exp_range
        return self

    def build(self) -> 'Product':
        return Product(
            home_id=self._home_id,
            barcode=self._barcode,
            original_name=self._original_name,
            quantity=self._quantity,
            location=self._location,
            nickname=self._nickname,
            expiration_date=self._expiration_date,
            expiration_range=self._expiration_range
        )


class Product:

    def builder(home_id: UUID, name: str, quantity: int, expiration_range: int) -> 'ProductBuilder':
        return ProductBuilder(home_id, name, quantity, expiration_range)
    
    NICKNAME_MAX_LENGTH = 20

    def __init__(self, 
                home_id: UUID,
                original_name: str,
                quantity: int, 
                expiration_range: int,
                barcode: Optional[str] = None,
                location: LocationType = LocationType.OTHER, 
                nickname: Optional[str] = None,
                expiration_date: Optional[date] = None):
        
        self._id = uuid4()
        self._home_id = home_id
        self._barcode = barcode
        self._original_name = original_name
        self.set_nickname(nickname)
        self.set_quantity(quantity)
        self._location = location
        self._expiration_dates_to_quantity = {} # expiration_date: (quantity, ExpirationType)
        self.set_expiration_date_and_type(expiration_date, quantity, expiration_range)

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

    def get_expiration_dates(self) -> Optional[date]:
        return self._expiration_dates_to_quantity 
    
    # Setters
    def set_nickname(self, new_nickname: str) -> None:
        if new_nickname is None:
            self._nickname = None
            return
        if self._is_valid_name(new_nickname):
            self._nickname = new_nickname    

    def set_expiration_date_and_type(self, expiration_date: Optional[date], quantity: int, expiration_range: int) -> None:
        if expiration_date is None:
            self._expiration_dates_to_quantity[expiration_date] = (quantity, ExpirationType.FRESH)
        else:
            days_until_expiration = (expiration_date - date.today()).days
            if days_until_expiration <= 0:
                expiration_type = ExpirationType.EXPIRED
            elif days_until_expiration <= expiration_range:
                expiration_type = ExpirationType.GOING_TO_EXPIRE
            else:
                expiration_type = ExpirationType.FRESH
            self._expiration_dates_to_quantity[expiration_date] = (quantity, expiration_type)
    
    def update_expiration_date(self, old_date: date, new_date: date, expiration_range: Optional[int]) -> None:
        if old_date in self._expiration_dates_to_quantity:
            quantity, _ = self._expiration_dates_to_quantity.pop(old_date)
            self.set_expiration_date_and_type(new_date, quantity, expiration_range)
        else:
            raise ValueError("Old expiration date not found.")
    
    def set_quantity(self, new_quantity: int) -> None:
        if new_quantity < 0:
            raise ValueError("Quantity cannot be negative.")
        self._quantity = new_quantity

    async def update_quantity_and_removal(self, expiration_date: date) -> None:
        if expiration_date in self._expiration_dates_to_quantity:
            date_quantity, _ = self._expiration_dates_to_quantity[expiration_date]
            del self._expiration_dates_to_quantity[expiration_date]
            self._quantity = self._quantity - date_quantity 
            return self._quantity
        else:
            raise ValueError(f"item of date {expiration_date} not found for this product.")
        
    async def update_quantity(self, expiration_date: date, new_quantity: int) -> None:
        if not isinstance(new_quantity, int):
            raise ValueError("Quantity must be a number.")
        if new_quantity < 0:
            raise ValueError("Quantity cannot be negative.")
        elif new_quantity == 0:
            return await self.update_quantity_and_removal(expiration_date)
        else:
            if expiration_date in self._expiration_dates_to_quantity:
                _, expiration_type = self._expiration_dates_to_quantity[expiration_date]
                self._expiration_dates_to_quantity[expiration_date] = (new_quantity, expiration_type)
                self._quantity = sum(q for q, _ in self._expiration_dates_to_quantity.values())
                return self._quantity
            else:
                raise ValueError(f"item of date {expiration_date} not found for this product.")

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
            "original_name": self._original_name,
            "nickname": self._nickname,
            "quantity": self._quantity,
            "location": self._location.name if self._location else None,
            "expiration_dates_to_quantity": {str(k): (v[0], str(v[1])) for k, v in self._expiration_dates_to_quantity.items()},
        }

         

