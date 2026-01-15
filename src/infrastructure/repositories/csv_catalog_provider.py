import csv
import os
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
        """
        Parses the CSV, populates data structures, and sorts the list
        to prioritize Global items and shorter names.
        """
        if not os.path.exists(csv_path):
            print(f"[WARNING] Catalog CSV file not found at: {csv_path}")
            return

        print(f"[INFO] Loading catalog data from {csv_path}...")
        
        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    barcode = row.get("Barcode", "").strip()
                    name = row.get("ItemName", "").strip()
                    chain = row.get("Chain", "GLOBAL").strip()
                    storage_location = row.get("SuggestedStoragelocation", "").strip()
                    if not barcode or not name:
                        continue
                        
                    item = CatalogItem(
                        barcode=barcode,
                        name=name,
                        manufacturer=row.get("ManufacturerName", ""),
                        chain_source=chain,
                        storage_location=storage_location
                    )
                    
                    self._all_items.append(item)

                    if chain == "GLOBAL":
                        self._global_map[barcode] = item
                    else:
                        key = f"{chain}_{barcode}"
                        self._chain_map[key] = item
            
            # SORTING LOGIC:
            # We sort the main list to prioritize better results during search.
            # 1. Global items appear first.
            # 2. Shortest names appear first (e.g., "Cucumber" is better than "Fresh Green Cucumber by Weight").
            self._all_items.sort(key=lambda x: (x.chain_source != "GLOBAL", len(x.name)))

            print(f"[INFO] Catalog loaded and sorted. Total items: {len(self._all_items)}")

        except Exception as e:
            print(f"[ERROR] Failed to load catalog CSV: {str(e)}")

    # =========================================================================
    # Interface Implementation
    # =========================================================================

    async def get_item_by_barcode(self, barcode: str, chain_name: Optional[str] = None) -> Optional[CatalogItem]:
        """
        Retrieves an item by barcode.
        """
        if chain_name:
            key = f"{chain_name}_{barcode}"
            chain_item = self._chain_map.get(key)
            if chain_item:
                return chain_item
        
        return self._global_map.get(barcode)
    
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