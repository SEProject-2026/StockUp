from abc import ABC, abstractmethod
from typing import List, Optional, Set
from src.domain.enums import ExpirationType, LocationType
from src.domain.product.product import Product
from uuid import UUID

class IProductRepository(ABC):
    """
    Interface defining the contract for Inventory (Home Products) data access.
    """

    @abstractmethod
    async def save(self, product: Product) -> None:
        """Creates a new inventory item."""
        pass

    @abstractmethod
    async def save_all(self, products: List[Product]) -> None:
        """Creates multiple inventory items in a batch operation."""
        pass

    @abstractmethod
    async def save_all_receipt(
        self,
        new_products: List[Product],
        updated_products: List[Product],
        new_item_ids: Set[UUID],
    ) -> None:
        """
        Receipt-optimized bulk save. Skips redundant re-queries by leveraging
        the caller's knowledge of which products/items are new vs existing.
        - new_products: Products that don't exist in DB yet (direct INSERT).
        - updated_products: Products already loaded from DB (only new items are inserted).
        - new_item_ids: IDs of ProductItems created during this receipt processing.
          Items whose IDs are NOT in this set were merged into existing items
          and need an atomic quantity UPDATE instead of INSERT.
        """
        pass

    @abstractmethod
    async def get_by_id(self, product_id: UUID) -> Optional[Product]:
        """Retrieves a single item by its ID."""
        pass

    @abstractmethod
    async def update(self, product: Product) -> None:
        """Updates an existing item (replaces the object)."""
        pass

    @abstractmethod
    async def delete(self, product_id: UUID) -> None:
        """Removes an item from the repository."""
        pass

    @abstractmethod
    async def list_all_by_home(self, home_id: UUID) -> List[Product]:
        """Retrieves all items belonging to a specific home."""
        pass

    @abstractmethod
    async def get_by_original_name(self, home_id: UUID, original_name: str) -> Optional[Product]:
        """Retrieves a product by its original name within a specific home."""
        pass

    @abstractmethod
    async def search_by_name(self, home_id: UUID, query: str) -> List[Product]:
        """Searches products in a home by name or nickname."""
        pass

    @abstractmethod
    async def get_by_location(self, home_id: UUID, location: str) -> List[Product]:
        """Retrieves products stored in a specific location within the home."""
        pass

    @abstractmethod  
    async def filter_products(
        self, 
        home_id: UUID, 
        query_text: Optional[str], 
        location: Optional[LocationType], 
        expiration_type: Optional[ExpirationType],
        warning_days: int
    ) -> List[Product]:
        """Filters products based on their expiration status."""
        pass