from uuid import UUID, uuid4
from typing import List, Optional, Dict
from datetime import date

from Domain.DomainServices.DomainException import DomainException
from Domain.SmartHome.Enums import ExpirationType, LocationType
from Domain.SmartHome.Product import Product

class Home:

    def __init__(self, user_id: UUID, id: UUID, name: str, join_code: str):
        self._id: UUID = id
        self._name: str = name
        self._join_code: str = join_code
        self._members: Dict[UUID, None] = {user_id: None}  # Dictionary of user IDs
        self._admin: UUID = user_id  # Admin user ID, assigned to creator by default
        self._join_requests: Dict[UUID, None] = {}  # Dictionary of user IDs requesting to join
        self._inventory: Dict[UUID, Product] = {}  # Dictionary of product IDs to Product objects

    def get_id(self) -> UUID:
        return self._id
    
    def get_name(self) -> str:
        return self._name
    
    def get_join_code(self) -> str:
        return self._join_code
    
    def get_members(self) -> Dict[UUID, None]:
        return self._members
    
    def get_admin(self) -> UUID:
        return self._admin
    
    def get_join_requests(self) -> Dict[UUID, None]:
        return self._join_requests
    
    def get_inventory(self) -> Dict[UUID, Product]:
        return self._inventory
    
    def set_name(self, name: str) -> None:
        self._name = name

    def assign_admin(self, user_id: UUID) -> None:
        if not self.is_member(user_id):
            raise ValueError("User must be a member to be assigned as admin.")
        self._admin = user_id

    def is_admin(self, user_id: UUID) -> bool:
        return self._admin == user_id
    
    def has_request_from(self, user_id: UUID) -> bool:
        return user_id in self._join_requests
    
    def add_join_request(self, user_id: UUID) -> None:
        if user_id in self._join_requests:
            raise ValueError("User has already requested to join.")
        self._join_requests[user_id] = None

    def remove_join_request(self, user_id: UUID) -> None:
        if user_id in self._join_requests:
            del self._join_requests[user_id]
        else:
            raise ValueError("No such join request found.")
        
    def add_member(self, user_id: UUID) -> None:
        if user_id in self._members:
            raise ValueError("User is already a member of the home.")
        self._members[user_id] = None

    def is_member(self, user_id: UUID) -> bool:
        return user_id in self._members
    
    def remove_member(self, user_id: UUID) -> None:
        if user_id in self._members:
            del self._members[user_id]
        else:
            raise ValueError("User is not a member of this home.")
        
    def add_to_inventory(self, product: Product) -> None:
        self._inventory[product.get_id()] = product

    def remove_from_inventory(self, product: Product) -> None:
        if product.get_id() in self._inventory:
            del self._inventory[product.get_id()]
        else:
            raise DomainException("Product not found in inventory.")
        
    def update_product_quantity(self, product_id: UUID, new_quantity: int) -> None:
        if product_id in self._inventory:
            product = self._inventory[product_id]
            product.set_quantity(new_quantity)
            self._inventory[product_id] = product
        else:
            raise DomainException("Product not found in inventory.")
        
    def update_expiration_date(self, product_id: UUID, new_date: date) -> None:
        if product_id in self._inventory:
            product = self._inventory[product_id]
            product.set_expiration_date(new_date)
            self._inventory[product_id] = product
        else:
            raise DomainException("Product not found in inventory.")
    
    def update_nickname(self, product_id: UUID, new_nickname: str) -> None:
        if product_id in self._inventory:
            # check for nickname uniqueness
            all_nicknames = [prod.get_nickname() for prod in self._inventory.values()]
            if new_nickname in all_nicknames:
                raise DomainException("Nickname already in use.")
            product = self._inventory[product_id]
            product.set_nickname(new_nickname)
            self._inventory[product_id] = product
        else:
            raise DomainException("Product not found in inventory.")

    def filter_by_expiration_type(self, filter_type: ExpirationType) -> Dict[UUID, Product]:
        filtered_inventory = {}
        for product_id, product in self._inventory.items():
            if filter_type == product.get_expiration_type():
                filtered_inventory[product_id] = product
        return filtered_inventory

    def filter_by_location(self, location: LocationType) -> Dict[UUID, Product]:
        filtered_inventory = {}
        for product_id, product in self._inventory.items():
            if product.get_location() == location:
                filtered_inventory[product_id] = product
        return filtered_inventory
    
    def search_product(self, query: str) -> Dict[UUID, Product]:
        found_products = {}
        for product_id, product in self._inventory.items():
            if query.lower() in product.get_nickname().lower():
                found_products[product_id] = product
            elif query.lower() in product.get_name().lower():
                found_products[product_id] = product
        return found_products