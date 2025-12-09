from enum import Enum, auto

class ExpirationType(Enum):
    FRESH = "תקין"
    GOING_TO_EXPIRE = "בקרוב יפוג"
    EXPIRED = "פג תוקף"

class Product:
    def __init__(self, id: str, name: str, nickname: str, quantity: int, location_id: int, expiration_type: ExpirationType):
        self._id = id
        self._name = name
        self._nickname = nickname
        self.quantity = quantity
        self.location_id = location_id
        self._expiration_type = expiration_type

    def get_id(self) -> str:
        return self._id

    def get_name(self) -> str:
        return self._name

    def get_nickname(self) -> str:
        return self._nickname

    def get_quantity(self) -> int:
        return self.quantity
    
    def get_location_id(self) -> int:
        return self.location_id
    
    def get_expiration_type(self) -> ExpirationType:
        return self._expiration_type    
    
    def set_nickname(self, new_nickname: str) -> None:
        self._nickname = new_nickname
    
    def set_expiration_date(self, new_date) -> None:
        self._expiration_type = new_date

    def set_expiration_type(self, new_expiration_type: ExpirationType) -> None:
        self._expiration_type = new_expiration_type
    
    def set_quantity(self, new_quantity: int) -> None:
        self.quantity = new_quantity

    def set_location_id(self, new_location_id: int) -> None:
        self.location_id = new_location_id
    

    