import csv
import os
import shutil
from tempfile import NamedTemporaryFile
from typing import List, Optional, Dict
from src.repositories.catalog_provider import ICatalogProvider, CatalogItem

class CsvCatalogProvider(ICatalogProvider):
    """
    Implementation of the Catalog Provider using a local CSV file.
    This implementation loads data into memory and includes logic to 
    deduplicate items by name during search to ensure a clean user experience.
    """

    def __init__(self, csv_path: str):
        """
        Initializes the provider and loads the data from the CSV file.
        
        Args:
            csv_path (str): The path to the master_db.csv file.
        """
        self._global_map: Dict[str, CatalogItem] = {}
        self._chain_map: Dict[str, CatalogItem] = {}
        self._all_items: List[CatalogItem] = []
        
        self._load_data(csv_path)

    def _load_data(self, csv_path: str):
        if not os.path.exists(csv_path):
            print(f"[WARNING] Catalog CSV file not found at: {csv_path}")
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

                    # Load weights and sample size if they exist
                    avg_w = row.get("AverageWeight", 0)
                    samp_s = row.get("SampleSize", 0)

                    item = CatalogItem(
                        barcode=barcode,
                        name=name,
                        manufacturer=row.get("ManufacturerName", ""),
                        chain_source=chain,
                        location=row.get("SuggestedStorageCategory", "OTHER").strip().upper() or "OTHER",
                        avg_weight=float(avg_w) if avg_w else 0.0,
                        sample_size=int(samp_s) if samp_s else 0
                    )

                    self._all_items.append(item)
                    if chain == "GLOBAL":
                        self._global_map[barcode] = item
                    else:
                        self._chain_map[f"{chain}_{barcode}"] = item

            # Sort for better search results
            self._all_items.sort(key=lambda x: (x.chain_source != "GLOBAL", len(x.name)))
            print(f"[INFO] Catalog loaded. Total items: {len(self._all_items)}")

        except Exception as e:
            print(f"[ERROR] Failed to load catalog: {e}")
    # =========================================================================
    # Interface Implementation
    # =========================================================================

    async def get_item_by_barcode(self, barcode: str, chain_name: Optional[str] = None) -> Optional[CatalogItem]:
        """
        Retrieves an item by barcode.
        """
        padded_barcode = "729" + "0" * (10 - len(barcode)) + barcode
        if chain_name:
            key = f"{chain_name}_{barcode}"
            item = self._chain_map.get(key)
            if item:
                return item
            
            item = self._chain_map.get(f"{chain_name}_{padded_barcode}")
            if item:
                return item
        item = self._global_map.get(barcode) or self._global_map.get(padded_barcode)
        return item
            
    
    async def get_items_by_barcodes(self, barcodes: List[str], chain_name: Optional[str] = None) -> List[CatalogItem]:
        """
        Retrieves multiple products by a list of barcodes.
        """
        results = []
        for barcode in barcodes:
            item = None
            
            # 1. Try chain specific first
            if chain_name:
                key = f"{chain_name}_{barcode}"
                item = self._chain_map.get(key)
            
            # 2. Fallback to global
            if not item:
                item = self._global_map.get(barcode)

            # 3. Fallback to padded barcode (for weight-based items)
            if not item and chain_name:
                key = f"{chain_name}_{"729" + "0" * (10 - len(barcode)) + barcode}"
                item = self._chain_map.get(key)
                if item:
                    item.barcode = barcode  # Adjust barcode to original

            # 4. Fallback to global padded barcode
            if not item:
                item = self._global_map.get("729" + "0" * (10 - len(barcode)) + barcode)
                if item:
                    item.barcode = barcode  # Adjust barcode to original
            
            if item:
                results.append(item)
                
        return results

    async def search_items_by_name(self, query: str) -> List[CatalogItem]:
        """
        Performs a text search and deduplicates results by name.
        """
        if not query or len(query) < 2:
            return []
        
        query = query.lower()
        results = []
        
        # Set to track names we have already added to the results
        seen_names = set()
        
        for item in self._all_items:
            if query in item.name.lower():
                
                # Normalize name to avoid minor duplicates
                clean_name = item.name.strip()
                
                # DEDUPLICATION LOGIC:
                # If we already have a product with this exact name, skip it.
                # Since the list is pre-sorted, the first occurrence is the "best" one
                # (either Global or the shortest name).
                if clean_name in seen_names:
                    continue
                
                results.append(item)
                seen_names.add(clean_name)
            
            if len(results) >= 20:
                break
                
        return results
    

    def update_weighted_mem_only(self, barcode: str, chain_name: str, measured_weight: float):
        """Updates internal memory object without touching the disk."""
        # Note: Using the internal sync helper for speed
        item = self._get_item_sync(barcode, chain_name or "GLOBAL")
        if not item:
            return
        
        old_total = item.avg_weight * item.sample_size
        item.sample_size += 1
        item.avg_weight = (old_total + measured_weight) / item.sample_size

    def persist(self):
        """Rewrites the entire CSV file (Once per receipt)."""
        self._save_to_csv_full()

    def _save_to_csv_full(self):
        """Rewrites the entire master database with atomic replacement."""
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
                        "AverageWeight": round(item.avg_weight, 3),
                        "SampleSize": item.sample_size
                    })
            
            # Atomic move: avoids corrupted files if the process crashes
            shutil.move(temp_file.name, self.csv_path)
        except Exception as e:
            if os.path.exists(temp_file.name):
                os.remove(temp_file.name)
            print(f"[ERROR] Failed to save catalog: {e}")

    async def search_items_by_name(self, query: str) -> List[CatalogItem]:
        if not query or len(query) < 2: return []
        query = query.lower()
        results, seen_names = [], set()
        
        for item in self._all_items:
            if query in item.name.lower():
                if item.name.strip() in seen_names: continue
                results.append(item)
                seen_names.add(item.name.strip())
            if len(results) >= 20: break
        return results