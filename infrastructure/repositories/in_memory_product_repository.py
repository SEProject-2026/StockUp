import uuid
from typing import Dict, List, Optional
from Repositories.IProductRepository import IProductRepository
from Domain.SmartHome.Product import Product



class InMemoryProductRepository(IProductRepository):
    def __init__(self):
        self._all_products: Dict = {}
    
    def save(self, product: Product) -> uuid.UUID:
        self._all_products[product.get_id()] = product
        return product.get_id()
    
    def get_by_id(self, product_id: uuid.UUID) -> Optional[Product]: 
        return self._all_products.get(product_id)
    
    def list_all(self) -> List[Product]:
        return list(self._all_products.values())
    
    def delete(self, product_id: uuid.UUID) -> None:
        if product_id in self._all_products:
            del self._all_products[product_id]
        else:
            raise KeyError("Product not found.")
    
    def get_next_id(self) -> uuid.UUID:
        return uuid.uuid4()
    
    def update(self, product: Product) -> None:
        self._all_products[product.get_id()] = product
    
    def clear(self):
        self._all_products.clear()