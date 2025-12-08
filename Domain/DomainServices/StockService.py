from datetime import date
from SmartHome import Product
from Domain.SmartHome import Home
from Domain import DomainException


class StockService:

    def __init__(self):
        self.all_stock = {}

    def add_product(self, home: Home, product_to_add: Product):
        if product_to_add.quantity <= 0:
            raise DomainException("Quantity must be greater than zero.")
        if product_to_add.expiration_date and product_to_add.expiration_date < date.today():
            raise DomainException("Expiration date cannot be in the past.")
        home.inventory.append(product_to_add)
        return home.inventory