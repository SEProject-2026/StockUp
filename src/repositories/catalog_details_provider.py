from abc import ABC, abstractmethod
from typing import Optional
from src.domain.smart_home.catalog_item import CatalogItem

class CatalogDetailsProvider(ABC):
    
    @abstractmethod
    async def get_product_details(self, barcode: str, chain: Optional[str] = None) -> Optional[CatalogItem]:
        """
        Retrieves product details.
        Logic:
        1. If chain_name is provided, looks for a chain-specific item (e.g. PLU code).
        2. If not found or chain_name is None, looks for a global item (EAN barcode).
        """
        pass
    
    @abstractmethod
    async def done(self) -> None:
        """
        Cleans up resources after all product details have been retrieved.
        """
        pass