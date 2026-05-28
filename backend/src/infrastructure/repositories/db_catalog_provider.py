from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from src.repositories.catalog_provider import ICatalogProvider, CatalogItem
from src.infrastructure.db.models import CatalogItemModel

class DbCatalogProvider(ICatalogProvider):
    def __init__(self, db: AsyncSession):
        self.db = db

    def _map_to_domain(self, db_item: CatalogItemModel) -> CatalogItem:
        """Converts DB model to Domain entity."""
        return CatalogItem(
            barcode=db_item.barcode,
            name=db_item.name,
            manufacturer=db_item.manufacturer,
            chain_source=db_item.chain,
            location=db_item.location,
            weight=db_item.avg_weight,
            sample_size=db_item.sample_size
        )

    def _get_padded_barcode(self, barcode: str) -> str:
        """Helper to pad barcodes to standard Israeli 13-digit format (729...)"""
        if len(barcode) >= 13:
            return barcode
        return "729" + "0" * (10 - len(barcode)) + barcode

    async def get_item_by_barcode(self, barcode: str, chain_name: Optional[str] = None) -> Optional[CatalogItem]:
        search_barcodes = [barcode, self._get_padded_barcode(barcode)]
        
        if chain_name:
            result = await self.db.execute(
                select(CatalogItemModel).where(
                    CatalogItemModel.barcode.in_(search_barcodes),
                    CatalogItemModel.chain == chain_name
                )
            )
            item = result.scalars().first()
            if item:
                r = self._map_to_domain(item)
                r.barcode = barcode
                return r
        
        result = await self.db.execute(
            select(CatalogItemModel).where(
                CatalogItemModel.barcode.in_(search_barcodes),
                CatalogItemModel.chain == "GLOBAL"
            )
        )
        item = result.scalars().first()
        if item:
            r = self._map_to_domain(item)
            r.barcode = barcode
            return r
        return None

    async def get_items_by_barcodes(self, barcodes: List[str], chain_name: Optional[str] = None) -> List[CatalogItem]:
        if not barcodes:
            return []

        barcode_mapping = {}
        all_search_terms = []
        for b in barcodes:
            padded = self._get_padded_barcode(b)
            all_search_terms.extend([b, padded])
            barcode_mapping[b] = b
            barcode_mapping[padded] = b

        filters = [CatalogItemModel.barcode.in_(all_search_terms)]
        if chain_name:
            filters.append(or_(CatalogItemModel.chain == chain_name, CatalogItemModel.chain == "GLOBAL"))
        else:
            filters.append(CatalogItemModel.chain == "GLOBAL")

        result = await self.db.execute(select(CatalogItemModel).where(*filters))
        db_items = list(result.scalars().all())
        
        results = []
        seen_original_barcodes = set()
        db_items.sort(key=lambda x: x.chain == "GLOBAL")

        for db_item in db_items:
            original = barcode_mapping.get(db_item.barcode)
            if original and original not in seen_original_barcodes:
                item = self._map_to_domain(db_item)
                item.barcode = original
                results.append(item)
                seen_original_barcodes.add(original)
                
        return results

    async def search_items_by_name(self, query: str) -> List[CatalogItem]:
        if not query or len(query) < 2:
            return []

        result = await self.db.execute(
            select(CatalogItemModel)
            .where(CatalogItemModel.name.ilike(f"%{query}%"))
            .order_by(CatalogItemModel.chain != "GLOBAL", CatalogItemModel.name)
            .limit(20)
        )
        db_items = result.scalars().all()
        return [self._map_to_domain(item) for item in db_items]

    async def update_weighted_mem_only(self, barcode: str, chain_name: str, measured_weight: float):
        """Updates the object and flushes changes to the DB buffer."""
        padded_barcode = "729" + "0" * (10 - len(barcode)) + barcode
        search_barcodes = [barcode, padded_barcode]

        result = await self.db.execute(
            select(CatalogItemModel).where(
                CatalogItemModel.barcode.in_(search_barcodes),
                CatalogItemModel.chain == (chain_name or "GLOBAL")
            )
        )
        db_item = result.scalars().first()
        if not db_item:
            result = await self.db.execute(
                select(CatalogItemModel).where(
                    CatalogItemModel.barcode.in_(search_barcodes),
                    CatalogItemModel.chain == "GLOBAL"
                )
            )
            db_item = result.scalars().first()
        if db_item:
            old_total = db_item.weight * db_item.sample_size
            db_item.sample_size += 1
            db_item.weight = (old_total + measured_weight) / db_item.sample_size
            self.db.add(db_item)
            await self.db.flush()

    async def persist(self):
        """Finalizes the database transaction."""
        try:
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            raise