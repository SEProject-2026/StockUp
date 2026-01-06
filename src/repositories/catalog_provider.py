from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

# === DTO (Data Transfer Object) ===
class CatalogItem(BaseModel):
    """
    Represents a read-only product definition from the master catalog.
    This is not a user inventory item, but a reference data object.
    """
    barcode: str
    name: str
    manufacturer: Optional[str] = None
    chain_source: str = "GLOBAL"  # Used for internal logic/debugging

    model_config = ConfigDict(from_attributes=True)

# === Interface ===
class ICatalogProvider(ABC):
    """
    Interface for retrieving product data.
    Allows switching between different data sources (CSV, Database, External API).
    """

    @abstractmethod
    async def get_item_by_barcode(self, barcode: str, chain_name: Optional[str] = None) -> Optional[CatalogItem]:
        """
        Retrieves a product by its barcode.
        
        Args:
            barcode: The barcode to search for.
            chain_name: (Optional) The specific retail chain context.
                        If provided, the provider attempts to find a chain-specific definition.
                        If not found (or not provided), it falls back to the global definition.
        """
        pass

    @abstractmethod
    async def search_items_by_name(self, query: str) -> List[CatalogItem]:
        """
        Performs a text-based search for products (e.g., for autocomplete).
        """
        pass