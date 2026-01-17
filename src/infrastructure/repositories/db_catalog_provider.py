from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from src.repositories.catalog_provider import ICatalogProvider, CatalogItem
from src.infrastructure.db.models import CatalogItemModel

class DbCatalogProvider(ICatalogProvider):
    def __init__(self, db: Session):
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
        # Create a list containing both the raw and the padded version
        search_barcodes = [barcode, self._get_padded_barcode(barcode)]
        
        # 1. Try to find chain-specific item (raw or padded)
        if chain_name:
            item = self.db.query(CatalogItemModel).filter(
                CatalogItemModel.barcode.in_(search_barcodes),
                CatalogItemModel.chain == chain_name
            ).first()
            if item:
                result = self._map_to_domain(item)
                result.barcode = barcode # Restore original barcode for consistency
                return result
        
        # 2. Fallback to GLOBAL (raw or padded)
        item = self.db.query(CatalogItemModel).filter(
            CatalogItemModel.barcode.in_(search_barcodes),
            CatalogItemModel.chain == "GLOBAL"
        ).first()
        
        if item:
            result = self._map_to_domain(item)
            result.barcode = barcode # Restore original barcode for consistency
            return result
            
        return None

    async def get_items_by_barcodes(self, barcodes: List[str], chain_name: Optional[str] = None) -> List[CatalogItem]:
        if not barcodes:
            return []

        # Map each barcode to its potential padded version
        # result_map stores: {padded_or_raw_barcode: original_barcode}
        barcode_mapping = {}
        all_search_terms = []
        for b in barcodes:
            padded = self._get_padded_barcode(b)
            all_search_terms.extend([b, padded])
            barcode_mapping[b] = b
            barcode_mapping[padded] = b

        # Optimization: Fetch all matching barcodes in one query
        filters = [CatalogItemModel.barcode.in_(all_search_terms)]
        if chain_name:
            filters.append(or_(CatalogItemModel.chain == chain_name, CatalogItemModel.chain == "GLOBAL"))
        else:
            filters.append(CatalogItemModel.chain == "GLOBAL")

        db_items = self.db.query(CatalogItemModel).filter(*filters).all()
        
        # We need to handle potential duplicates (if both raw and padded exist)
        # and ensure we return the original barcode requested.
        results = []
        seen_original_barcodes = set()
        
        # Sort results: Prefer chain-specific over GLOBAL
        db_items.sort(key=lambda x: x.chain == "GLOBAL")

        for db_item in db_items:
            original = barcode_mapping.get(db_item.barcode)
            if original and original not in seen_original_barcodes:
                item = self._map_to_domain(db_item)
                item.barcode = original # Restore the barcode the user actually scanned
                results.append(item)
                seen_original_barcodes.add(original)
                
        return results

    async def search_items_by_name(self, query: str) -> List[CatalogItem]:
        if not query or len(query) < 2:
            return []

        # Using ILIKE for case-insensitive search in Postgres
        # Optimized with the index we created on ItemName
        db_items = (
            self.db.query(CatalogItemModel)
            .filter(CatalogItemModel.name.ilike(f"%{query}%"))
            .order_by(CatalogItemModel.chain != "GLOBAL", CatalogItemModel.name)
            .limit(20)
            .all()
        )

        return [self._map_to_domain(item) for item in db_items]

    def update_weighted_mem_only(self, barcode: str, chain_name: str, measured_weight: float):
        """Updates the object and flushes changes to the DB buffer."""
        padded_barcode = "729" + "0" * (10 - len(barcode)) + barcode
        search_barcodes = [barcode, padded_barcode]

        # 1. Fetch the item
        db_item = self.db.query(CatalogItemModel).filter(
            CatalogItemModel.barcode.in_(search_barcodes),
            CatalogItemModel.chain == (chain_name or "GLOBAL")
        ).first()
        if not db_item:
            db_item = self.db.query(CatalogItemModel).filter(
                CatalogItemModel.barcode.in_(search_barcodes),
                CatalogItemModel.chain == "GLOBAL"
            ).first()
        if db_item:
            # 2. Perform calculation
            old_total = db_item.weight * db_item.sample_size
            db_item.sample_size += 1
            db_item.weight = (old_total + measured_weight) / db_item.sample_size
            
            # 3. Force synchronization
            # Ensure the item is attached to the current session
            self.db.add(db_item)
            
            # Push changes to the database transaction (but don't commit yet)
            self.db.flush()
            

    def persist(self):
        """Finalizes the database transaction."""
        try:
            # We don't check for 'dirty' here because flush() might have already 
            # moved objects from 'dirty' to the database buffer.
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise