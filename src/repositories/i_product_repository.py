from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.smart_home.enums import ExpirationType
from src.domain.smart_home.product import Product
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
    async def search_by_name(self, home_id: UUID, query: str) -> List[Product]:
        """Searches products in a home by name or nickname."""
        pass

    @abstractmethod
    # might delete later if not needed    
    async def get_by_expiration_filter(self, home_id: UUID, home_expiration_range: int, filter_type: ExpirationType) -> List[Product]:
        """
        Retrieves products based on expiration status.
        filter_type options: 'EXPIRED', 'NEAR_EXPIRATION', 'FRESH'
        """
        pass

    @abstractmethod
    async def get_by_location(self, home_id: UUID, location: str) -> List[Product]:
        """Retrieves products stored in a specific location within the home."""
        pass