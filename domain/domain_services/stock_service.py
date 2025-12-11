from datetime import date
from typing import Dict
from uuid import uuid4, UUID
from domain import User
from domain.smart_home.enums import LocationType, ExpirationType
from domain.smart_home.product import Product
from domain.smart_home.home import Home
from domain.domain_services.domain_exception import DomainException
from response import Response

nickname_max_length = 20

class StockService:

    def __init__(self):
        pass

    def add_product(self, user_id: UUID, home: Home, product_to_add: Product) -> None:
        if not home.is_member(user_id):
            raise DomainException("User does not belong to this home.")
        if product_to_add.get_quantity() <= 0:
            raise DomainException("Quantity must be greater than zero.")
        if product_to_add.get_expiration_date() is not None and product_to_add.get_expiration_date() < date.today():
            raise DomainException("Expiration date cannot be in the past.")
        home.add_to_inventory(product_to_add)
    
    def remove_product(self, user_id: UUID, home: Home, product_to_remove: Product) -> None:  
        if not home.is_member(user_id):
            raise DomainException("User does not belong to this home.")
        home.remove_from_inventory(product_to_remove)
    
    def update_quantity(self, user_id: UUID, home: Home, product_id, new_quantity: int) -> None:
        if not home.is_member(user_id):
            raise DomainException("User does not belong to this home.")
        if new_quantity < 0:
            raise DomainException("Quantity cannot be negative.")
        home.update_product_quantity(product_id, new_quantity)
        
    
    def update_expiration_date(self, user_id: UUID, home: Home, product_id, new_date: date) -> None:
        if not home.is_member(user_id):
            raise DomainException("User does not belong to this home.")
        if new_date < date.today():
            raise DomainException("Expiration date cannot be in the past.")
        home.update_expiration_date(product_id, new_date)
    
    def update_nickname(self, user_id: UUID, home: Home, product_id, new_nickname: str) -> None:
        if not home.is_member(user_id):
            raise DomainException("User does not belong to this home.")
        if new_nickname.strip() == "":
            raise DomainException("Nickname cannot be empty.")
        if len(new_nickname) > nickname_max_length:
            raise DomainException("Nickname is too long.")
        if not self.is_valid_name(new_nickname):
            raise DomainException("Nickname contains invalid characters, must have only letters, numbers, and single spaces.")
        home.update_nickname(product_id, new_nickname)
    
    def is_valid_name(new_nickname: str) -> bool:
        if "  " in new_nickname:
            return False
        if not new_nickname.replace(" ", "").replace("%", "").isalnum():
            return False
        return True
    
    def filter_by_expiration_type(self, user_id: UUID, home: Home, filter_type: str) -> Response[Dict[UUID, Product]]:
        if not home.is_member(user_id):
            raise DomainException("User does not belong to this home.")
        filter_type: ExpirationType = ExpirationType(filter_type)
        filtered_inventory = home.filter_by_expiration_type(filter_type)
        if len(filtered_inventory) == 0:
            return Response(isOk = True, data = "No products found for the selected filter type.")
        return Response(isOk = True, data = filtered_inventory)
    
    def filter_by_location(self, user_id: UUID, home: Home, location: LocationType) -> Response[Dict[UUID, Product]]:
        if not home.is_member(user_id):
            raise DomainException("User does not belong to this home.")    
        filtered_inventory = home.filter_by_location(location)
        if len(filtered_inventory) == 0:
            return Response(isOk = True, data = "No products found for the selected location.")
        return Response(isOk = True, data = filtered_inventory)
    
    def search_product(self, user_id: UUID, home: Home, query: str) -> Dict[UUID, Product]:
        if not home.is_member(user_id):
            raise DomainException("User does not belong to this home.")
        if not query or query.strip() == "":
            raise DomainException("Search cannot be empty.")
        found_products = home.search_product(query)
        return found_products