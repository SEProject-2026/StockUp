from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.shopping_list.shopping_list import ShoppingList

class IShoppingListRepository(ABC):
    """
    Interface defining the contract for Shopping List and Base Mode data access.
    Follows a state-based approach where entire lists/configs are updated.
    """

    # --- Active Shopping List ---

    @abstractmethod
    async def save(self, shopping_list: ShoppingList) -> None:
        """Persists or updates the entire shopping list state for a home."""
        pass

    @abstractmethod
    async def get_by_id(self, id: UUID) -> Optional[ShoppingList]:
        """Retrieves the current shopping list entity for a specific home."""
        pass

    @abstractmethod
    async def get_all_by_home(self, home_id: UUID) -> List[ShoppingList]:
        pass

    @abstractmethod
    async def delete(self, id: UUID) -> None:
        """Removes the entire shopping list record."""
        pass
