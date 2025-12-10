from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from Domain.SmartHome.Product import Product
from uuid import UUID

class IProductRepository(ABC):
    """
    Interface defining the contract for Inventory data access.
    """

    @abstractmethod
    def save(self, product: Product) -> UUID:
        """
        Creates a new inventory item.
        Returns: The ID of the new item.
        """
        pass

    @abstractmethod
    def get_by_id(self, item_id: UUID) -> Optional[Product]:
        """
        Retrieves a single item by its ID.
        Returns: The item data if found, or None.
        """
        pass

    
    def list_all(self) -> List[Product]:
        """
        Retrieves all items in the inventory.
        Returns: A list of items (can be empty).
        """
        pass

    @abstractmethod
    def update(self, item_id: UUID, updates: Dict) -> bool:
        """
        Updates an existing item.
        Returns: True if successful, False if item not found.
        """
        pass

    @abstractmethod
    def delete(self, item_id: UUID) -> None:
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
    
    # need to implement in InMemoryProductRepository.py
    @abstractmethod
    def get_product_name_by_barcode(self, barcode: str, company_name: str) -> str:
        """
        Retrieves the product name associated with a given barcode.
        Returns: The product name as a string.
        """
        pass