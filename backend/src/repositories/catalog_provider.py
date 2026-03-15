from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from src.domain.enums import LocationType

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
    location: Optional[LocationType] = LocationType.OTHER
    weight: Optional[float] = None  
    sample_size: Optional[int] = None

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
    async def get_items_by_barcodes(self, barcodes: List[str], chain_name: Optional[str] = None) -> List[CatalogItem]:
        """
        Retrieves multiple products by a list of barcodes.
        Optimized for batch operations to avoid N+1 queries.

        Args:
            barcodes: A list of barcode strings to search for.
            chain_name: (Optional) The specific retail chain context.

        Returns:
            List[CatalogItem]: A list of found products. Barcodes that are not found are typically skipped.
        """
        pass

    @abstractmethod
    async def search_items_by_name(self, query: str) -> List[CatalogItem]:
        """
        Performs a text-based search for products (e.g., for autocomplete).
        """
        pass

    @abstractmethod
    def update_weighted_mem_only(self, barcode: str, chain_name: str, measured_weight: float):
        """
        Updates the in-memory weighted average for a product's weight.
        This does not persist changes to the underlying data source.

        Args:
            barcode: The barcode of the product to update.
            chain_name: The retail chain context.
            measured_weight: The new weight measurement to incorporate.
        """
        pass
    @abstractmethod
    def persist(self):
        """Persists all changes made in memory/session to the underlying storage."""
        pass