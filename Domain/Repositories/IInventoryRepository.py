from abc import ABC, abstractmethod
from typing import List, Optional, Dict

class IInventoryRepository(ABC):
    """
    Interface defining the contract for Inventory data access.
    """

    @abstractmethod
    def save(self, item_data: Dict) -> int:
        """
        Creates a new inventory item.
        Returns: The ID of the new item.
        """
        pass

    @abstractmethod
    def get_by_id(self, item_id: int) -> Optional[Dict]:
        """
        Retrieves a single item by its ID.
        Returns: The item data if found, or None.
        """
        pass

    
    def list_all(self) -> List[Dict]:
        """
        Retrieves all items in the inventory.
        Returns: A list of items (can be empty).
        """
        pass

    @abstractmethod
    def update(self, item_id: int, updates: Dict) -> bool:
        """
        Updates an existing item.
        Returns: True if successful, False if item not found.
        """
        pass

    @abstractmethod
    def delete(self, item_id: int) -> None:
        """
        Removes an item from the repository.
        Returns: None (Raises an exception if deletion fails).
        """
        pass

    @abstractmethod
    def get_next_id(self) -> int:
        """
        Retrieves the next available unique identifier for a new inventory item.
        Returns: An integer representing the next unique ID.
        """
        pass