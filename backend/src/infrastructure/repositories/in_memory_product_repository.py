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
        self._products_db[product.id] = product

    async def save_all(self, products: List[Product]) -> None:
        for product in products:
            self._products_db[product.id] = product
    
    async def get_by_id(self, product_id: uuid.UUID) -> Optional[Product]: 
        return self._products_db.get(product_id)
    
    async def get_by_original_name(self, home_id: uuid.UUID, original_name: str) -> Optional[Product]:
        """
        Finds a product by its original name within a specific home.
        """
        for p in self._products_db.values():
            if p.home_id == home_id and p.original_name == original_name:
                return p
        return None
    
    async def update(self, product: Product) -> None:
        if product.id in self._products_db:
            self._products_db[product.id] = product
        else:
            raise KeyError(f"Product {product.id} not found for update.")
            
    async def delete(self, product_id: uuid.UUID) -> None:
        if product_id in self._products_db:
            del self._products_db[product_id]
        else:
            raise KeyError(f"Product {product_id} not found for deletion.")

    async def list_all_by_home(self, home_id: uuid.UUID) -> List[Product]:
        return [
            p for p in self._products_db.values() 
            if p.home_id == home_id
        ]

    async def search_by_name(self, home_id: uuid.UUID, query: str) -> List[Product]:
        query = query.lower()
        results = []
        for p in self._products_db.values():
            if p.home_id != home_id:
                continue
            
            # Check original name
            name_match = query in p.original_name.lower()
            
            # Check nickname (if exists)
            nickname_match = p.nickname and query in p.nickname.lower()
            
            if name_match or nickname_match:
                results.append(p)
        return results
    
    async def get_by_location(self, home_id: uuid.UUID, location: LocationType) -> List[Product]:
        """
        Returns products that have AT LEAST one item in the requested location.
        """
        results = []
        for p in self._products_db.values():
            if p.home_id != home_id:
                continue
            
            # Check if ANY item in this product is in the requested location
            has_item_in_location = any(item.location == location for item in p.items)
            
            if has_item_in_location:
                results.append(p)
                
        return results

    async def clear(self):
        self._products_db.clear()