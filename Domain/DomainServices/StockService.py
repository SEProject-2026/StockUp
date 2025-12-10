from datetime import date
from typing import Dict
import uuid
from Domain import User
from Domain.SmartHome import Product
from Domain.SmartHome import Home
from Domain.DomainServices import DomainException
import Response

nickname_max_length = 20

class StockService:

    def __init__(self):
        pass

    def add_product(self, user: User, home: Home, product_to_add: Product) -> Dict[uuid.UUID, Product]:
        if user is None:
            raise DomainException("User not found in system")
        if home is None:
            raise DomainException("Home not found in system")
        if user.get_id() not in home.get_members():
            raise DomainException("User does not belong to this home.")
        if product_to_add.quantity <= 0:
            raise DomainException("Quantity must be greater than zero.")
        if product_to_add.expiration_date and product_to_add.expiration_date < date.today():
            raise DomainException("Expiration date cannot be in the past.")
        home.get_inventory()[product_to_add.get_id()] = product_to_add
        return home.get_inventory()
    
    def remove_product(self, user: User, home: Home, product_to_remove: Product) -> Dict[uuid.UUID, Product]:
        if user is None:
            raise DomainException("User not found in system")
        if home is None:
            raise DomainException("Home not found in system")     
        if user.get_id() not in home.get_members():
            raise DomainException("User does not belong to this home.")
        if home.get_inventory().get(product_to_remove.get_id()) is None:
            raise DomainException("Product not found in home inventory.")
        del home.get_inventory()[product_to_remove.get_id()]
        return home.get_inventory()
    
    def update_quantity(self, user_id: uuid.UUID, home: Home, product_id, new_quantity: int) -> Dict[uuid.UUID, Product]:
        if user_id not in home.get_members():
            raise DomainException("User does not belong to this home.")
        product = home.get_inventory().get(product_id)
        if product is None:
            raise DomainException("Product not found in home inventory.")
        if user_id not in home.get_members():
            raise DomainException("User does not belong to this home.")
        if new_quantity < 0:
            raise DomainException("Quantity cannot be negative.")
        product.set_quantity(new_quantity)
        home.get_inventory()[product_id] = product
        return home.get_inventory()
    
    def update_expiration_date(self, user_id: uuid.UUID, home: Home, product_id, new_date: date) -> Dict[uuid.UUID, Product]:
        if user_id not in home.get_members():
            raise DomainException("User does not belong to this home.")
        product = home.get_inventory().get(product_id)
        if product is None:
            raise DomainException("Product not found in home inventory.")
        if user_id not in home.get_members():
            raise DomainException("User does not belong to this home.")
        if new_date < date.today():
            raise DomainException("Expiration date cannot be in the past.")
        product.set_expiration_date(new_date)
        home.get_inventory()[product_id] = product
        return home.get_inventory()
    
    def update_nickname(self, user_id: uuid.UUID, home: Home, product_id, new_nickname: str) -> Dict[uuid.UUID, Product]:
        if user_id not in home.get_members():
            raise DomainException("User does not belong to this home.")
        product = home.get_inventory().get(product_id)
        if new_nickname.strip() == "":
            raise DomainException("Nickname cannot be empty.")
        if len(new_nickname) > nickname_max_length:
            raise DomainException("Nickname is too long.")
        if product is None:
            raise DomainException("Product not found in home inventory.")
        if not self.is_valid_name(new_nickname):
            raise DomainException("Nickname contains invalid characters, must have only letters, numbers, and single spaces.")
        all_nicknames = [prod.get_nickname() for prod in home.get_inventory().values()]
        if new_nickname in all_nicknames:
            raise DomainException("Nickname already in use.")
        product.set_nickname(new_nickname)
        home.get_inventory()[product_id] = product
        return home.get_inventory()
    
    def is_valid_name(new_nickname: str) -> bool:
        if "  " in new_nickname:
            return False
        if not new_nickname.replace(" ", "").replace("%", "").isalnum():
            return False
        return True
    
    def filter_by_expiration_type(self, user_id: uuid.UUID, home: Home, filter_type: str) -> Response[Dict[uuid.UUID, Product]]:
        if user_id not in home.get_members():
            raise DomainException("User does not belong to this home.")
        filter_type = Product.ExpirationType[filter_type]
        filtered_inventory = {}
        for product_id, product in home.get_inventory().items():
            if filter_type ==  product.get_expiration_type():
                filtered_inventory[product_id] = product
        if len(filtered_inventory) == 0:
            return Response(isOk = True, data = "No products found for the selected filter type.")
    
    def filter_by_location(self, user_id: uuid.UUID, home: Home, location_id: str) -> Response[Dict[uuid.UUID, Product]]:
        if user_id not in home.get_members():
            raise DomainException("User does not belong to this home.")
        try:
            location_id = int(location_id)
        except ValueError:
            raise DomainException("Invalid location.")    
        filtered_inventory = {}
        for product_id, product in home.get_inventory().items():
            if product.get_location_id() == location_id:
                filtered_inventory[product_id] = product
        if len(filtered_inventory) == 0:
            return Response(isOk = True, data = "No products found for the selected location.")
        return Response(isOk = True, data = filtered_inventory)
    
    def filter_by_category(self, user_id: uuid.UUID, home: Home, location_id: str) -> Response[Dict[uuid.UUID, Product]]:
        if user_id not in home.get_members():
            raise DomainException("User does not belong to this home.")
        filtered_inventory = {}
        for product_id, product in home.get_inventory().items():
            if product.get_location_id() == location_id:
                filtered_inventory[product_id] = product
        if len(filtered_inventory) == 0:
            return Response(isOk = True, data = "No products found for the selected category.")
        return Response(isOk = True, data = filtered_inventory)
    
    def search_product(self, user_id: uuid.UUID, home: Home, query: str) -> Dict[uuid.UUID, Product]:
        if user_id not in home.get_members():
            raise DomainException("User does not belong to this home.")
        if not query or query.strip() == "":
            raise DomainException("Search cannot be empty.")
        found_products = {}
        for product_id, product in home.get_inventory().items():
            if product.get_nickname().lower() in query.lower():
                found_products[product_id] = product
            if product.get_name().lower() in query.lower():
                found_products[product_id] = product
        return found_products