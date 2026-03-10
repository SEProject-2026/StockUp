from abc import ABC, abstractmethod
from typing import List, Optional
from backend.src.domain.smart_home.enums import ExpirationType
from backend.src.domain.smart_home.product import Product
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
    async def adjust_quantity_and_cleanup(self, product_id: UUID, item_id: UUID, delta: int) -> Optional[Product]:
        """
        Adjusts the quantity of a specific line item and performs cleanup if quantity drops to 0 or below.
        Returns the updated product, or None if the product was deleted.
        """
        pass

    @abstractmethod
    async def remove_item_and_cleanup(self, product_id: UUID, item_id: UUID) -> Optional[Product]:
        """
        Completely removes a specific line item and performs cleanup if total quantity drops to 0 or below.
        Returns the updated product, or None if the product was deleted.
        """
        pass