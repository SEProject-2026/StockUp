import csv
import os
import shutil
from tempfile import NamedTemporaryFile
from typing import List, Optional, Dict
from backend.src.repositories.catalog_provider import ICatalogProvider, CatalogItem

class CsvCatalogProvider(ICatalogProvider):
    """
    Implementation of the Catalog Provider using a local CSV file.
    Includes logic for memory-only updates and atomic persistence.
    """

    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self._global_map: Dict[str, CatalogItem] = {}
        self._chain_map: Dict[str, CatalogItem] = {}
        self._all_items: List[CatalogItem] = []
        
        self._load_data(csv_path)

    def _load_data(self, csv_path: str):
        """Loads the entire CSV into memory maps."""
        if not os.path.exists(csv_path):
            return

        self._global_map = {}
        self._chain_map = {}
        self._all_items = []

        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    barcode = row.get("Barcode", "").strip()
                    name = row.get("ItemName", "").strip()
                    chain = row.get("Chain", "GLOBAL").strip()
                    
                    if not barcode or not name:
                        continue

                    item = CatalogItem(
                        barcode=barcode,
                        name=name,
                        manufacturer=row.get("ManufacturerName", ""),
                        chain_source=chain,
                        location=row.get("SuggestedStorageCategory", "OTHER").strip().upper() or "OTHER",
                        weight=float(row.get("AverageWeight", 0) or 0),
                        sample_size=int(row.get("SampleSize", 0) or 0)
                    )

                    self._all_items.append(item)
                    if chain == "GLOBAL":
                        self._global_map[barcode] = item
                    else:
                        self._chain_map[f"{chain}_{barcode}"] = item

            # Sort: Prioritize GLOBAL items and shorter names for search relevance
            self._all_items.sort(key=lambda x: (x.chain_source != "GLOBAL", len(x.name)))

        except Exception as e:{}

    def _get_padded_barcode(self, barcode: str) -> str:
        """Helper to pad barcodes to standard 13-digit format (729...)"""
        if len(barcode) >= 13 or not barcode.isdigit():
            return barcode
        return "729" + "0" * (10 - len(barcode)) + barcode

    def _get_item_sync(self, barcode: str, chain_name: Optional[str] = None) -> Optional[CatalogItem]:
        """Internal synchronous helper with padding support."""
        padded = self._get_padded_barcode(barcode)
        
        # 1. Try chain-specific (raw or padded)
        if chain_name and chain_name != "GLOBAL":
            item = self._chain_map.get(f"{chain_name}_{barcode}") or \
                   self._chain_map.get(f"{chain_name}_{padded}")
            if item: return item

        # 2. Try global (raw or padded)
        return self._global_map.get(barcode) or self._global_map.get(padded)

    # === ICatalogProvider Implementation ===

    async def get_item_by_barcode(self, barcode: str, chain_name: Optional[str] = None) -> Optional[CatalogItem]:
        return self._get_item_sync(barcode, chain_name)

    async def get_items_by_barcodes(self, barcodes: List[str], chain_name: Optional[str] = None) -> List[CatalogItem]:
        results = []
        for b in barcodes:
            item = self._get_item_sync(b, chain_name)
            if item:
                # Ensure we return a copy or adjust barcode if it was found via padding
                results.append(item)
        return results

    async def search_items_by_name(self, query: str) -> List[CatalogItem]:
        if not query or len(query) < 2: return []
        query = query.lower()
        results, seen_names = [], set()
        
        for item in self._all_items:
            clean_name = item.name.strip()
            if query in item.name.lower() and clean_name not in seen_names:
                results.append(item)
                seen_names.add(clean_name)
            if len(results) >= 20: break
        return results

    def update_weighted_mem_only(self, barcode: str, chain_name: str, measured_weight: float):
        """Updates internal memory object with moving average logic."""
        item = self._get_item_sync(barcode, chain_name)
        if not item:
            return
        
        old_total = item.weight * item.sample_size
        item.sample_size += 1
        item.weight = (old_total + measured_weight) / item.sample_size

    def persist(self):
        """Finalizes changes by rewriting the CSV file."""
        fields = [
            "Barcode", "ItemName", "ManufacturerName", 
            "Chain", "SuggestedStorageCategory", 
            "AverageWeight", "SampleSize"
        ]
        
        temp_file = NamedTemporaryFile(mode='w', delete=False, encoding='utf-8-sig', newline='')
        try:
            with temp_file as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                for item in self._all_items:
                    writer.writerow({
                        "Barcode": item.barcode,
                        "ItemName": item.name,
                        "ManufacturerName": item.manufacturer,
                        "Chain": item.chain_source,
                        "SuggestedStorageCategory": item.location,
                        "AverageWeight": round(item.weight, 3),
                        "SampleSize": item.sample_size
                    })
            
            shutil.move(temp_file.name, self.csv_path)
        except Exception as e:
            if os.path.exists(temp_file.name):
                os.remove(temp_file.name)