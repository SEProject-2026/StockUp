from abc import ABC, abstractmethod
from typing import Optional
from domain.smart_home.catalog_item import CatalogItem
from domain.smart_home.enums import ChainType

class ICatalogRepository(ABC):
    
    @abstractmethod
    async def get_product_details(self, barcode: str, chain: Optional[ChainType] = None) -> Optional[CatalogItem]:
        """
        Retrieves product details.
        Logic:
        1. If chain_name is provided, looks for a chain-specific item (e.g. PLU code).
        2. If not found or chain_name is None, looks for a global item (EAN barcode).
        """
        pass