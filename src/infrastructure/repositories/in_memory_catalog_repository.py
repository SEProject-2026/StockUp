from typing import Optional
from src.repositories.i_catalog_repositoy import ICatalogRepository
from src.domain.smart_home.catalog_item import CatalogItem
from src.domain.smart_home.enums import ChainType

class InMemoryCatalogRepository(ICatalogRepository):
    
    def __init__(self):
        pass

    async def get_product_details(self, barcode: str, chain_type: Optional[ChainType] = None) -> Optional[CatalogItem]:
       pass