import uuid
from typing import Dict, List, Optional
from src.domain.smart_home.enums import ExpirationType, LocationType
from src.repositories.i_product_repository import IProductRepository
from src.domain.smart_home.product import Product

class InMemoryProductRepository(IProductRepository):
    
    def __init__(self):
        # Key: product_id, Value: Product Object
        self._products_db: Dict[uuid.UUID, Product] = {}
    
    async def save(self, product: Product) -> None:
        self._products_db[product.get_id()] = product
    
    async def get_by_id(self, product_id: uuid.UUID) -> Optional[Product]: 
        return self._products_db.get(product_id)
    
    async def update(self, product: Product) -> None:
        if product.get_id() in self._products_db:
            self._products_db[product.get_id()] = product
        else:
            raise KeyError("Product not found for update.")
            
    async def delete(self, product_id: uuid.UUID) -> None:
        if product_id in self._products_db:
            del self._products_db[product_id]
        else:
            raise KeyError("Product not found for deletion.")

    async def list_all_by_home(self, home_id: uuid.UUID) -> List[Product]:
        return [
            p for p in self._products_db.values() 
            if p.get_home_id() == home_id
        ]

    async def search_by_name(self, home_id: uuid.UUID, query: str) -> List[Product]:
        query = query.lower()
        results = []
        for p in self._products_db.values():

            if p.get_home_id() != home_id:
                continue
            name_match = query in p.get_name().lower()
            nickname_match = p.get_nickname() and query in p.get_nickname().lower()
            
            if name_match or nickname_match:
                results.append(p)
        return results

    async def get_by_expiration_filter(self, home_id: uuid.UUID, filter_type: ExpirationType) -> List[Product]:
        results = []

        for p in self._products_db.values():
            if p.get_home_id() != home_id:
                continue
            
            exp_type = p.get_expiration_type()
            if exp_type == filter_type:
                results.append(p)
        return results
    
    async def get_by_location(self, home_id: uuid.UUID, location: LocationType) -> List[Product]:
        results = []
        for p in self._products_db.values():
            if p.get_home_id() != home_id:
                continue
            
            if p.get_location() == location:
                results.append(p)
        return results

    async def clear(self):
        self._products_db.clear()