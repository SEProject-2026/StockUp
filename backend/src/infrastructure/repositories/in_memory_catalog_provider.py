from typing import List, Optional
from src.repositories.catalog_provider import ICatalogProvider, CatalogItem

class InMemoryCatalogProvider(ICatalogProvider):
    """
    In-memory fallback implementation of the Catalog Provider.
    Used for local testing or when a live database session is not provided.
    """
    def __init__(self, items: Optional[List[CatalogItem]] = None):
        self.items = items or []

    async def get_item_by_barcode(self, barcode: str, chain_name: Optional[str] = None) -> Optional[CatalogItem]:
        for item in self.items:
            if item.barcode == barcode:
                return item
        return None

    async def get_items_by_barcodes(self, barcodes: List[str], chain_name: Optional[str] = None) -> List[CatalogItem]:
        results = []
        for b in barcodes:
            item = await self.get_item_by_barcode(b, chain_name)
            if item:
                results.append(item)
        return results

    async def search_items_by_name(self, query: str) -> List[CatalogItem]:
        if not query or len(query) < 2:
            return []
        query_lower = query.lower()
        results = []
        for item in self.items:
            if query_lower in item.name.lower():
                results.append(item)
        return results

    def update_weighted_mem_only(self, barcode: str, chain_name: str, measured_weight: float):
        """No-op for in-memory catalog updates."""
        pass

    def persist(self):
        """No-op for in-memory catalog provider persistence."""
        pass
