from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.shopping_list.base_mode import BaseMode
from src.domain.shopping_list.shopping_list import ShoppingList

class IShoppingListRepository(ABC):
    """
    Interface defining the contract for Shopping List and Base Mode data access.
    Follows a state-based approach where entire lists/configs are updated.
    """

    # --- Active Shopping List ---

    @abstractmethod
    async def save_list(self, shopping_list: ShoppingList) -> None:
        """Persists or updates the entire shopping list state for a home."""
        pass

    @abstractmethod
    async def get_list_by_home(self, home_id: UUID) -> Optional[ShoppingList]:
        """Retrieves the current shopping list entity for a specific home."""
        pass

    @abstractmethod
    async def delete_list(self, home_id: UUID) -> None:
        """Removes the entire shopping list record."""
        pass

    # --- Base Mode Configuration ---

    @abstractmethod
    async def save_base_mode(self, base_mode: BaseMode) -> None:
        """Persists or updates the entire Base Mode configuration state."""
        pass

    @abstractmethod
    async def get_base_mode_by_home(self, home_id: UUID) -> Optional[BaseMode]:
        """Retrieves the Base Mode configuration entity for a specific home."""
        pass