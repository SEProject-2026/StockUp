# src/infrastructure/scanner/receipt_scanner.py
from src.infrastructure.google_scanner.scanner import scan_receipt, merge_receipts

class ReceiptScanner:
    def parse_receipt(self,all_paths: list) -> tuple[str, dict]:
        """
        Parses one or more receipt images and merges them.
        """
        # Scan all slices
        all_paths.reverse() 
        parsed_slices = []
        
        for path in all_paths:
            # Using the core function from your scanner.py
            result = scan_receipt(path)
            parsed_slices.append(result)
            
        # Merge if there are multiple parts (Panorama Stitching)
        if len(parsed_slices) > 1:
            final_data = merge_receipts(parsed_slices)
        else:
            final_data = parsed_slices[0]
            
        # The service expects (chain_name, items_dict)
        chain_name = final_data.get("chain", "Unknown")
        
        # Transform products list to the dictionary format the service expects:
        # { barcode: (quantity, unit_str) }
        scanned_items = {}
        for product in final_data.get("products", []):
            barcode = product.get("barcode")
            qty = product.get("quantity", 1.0)
            unit_str = product.get("unit", "UNIT")
            if(scanned_items.get(barcode)):
                # If the barcode already exists, we sum the quantities
                existing_qty = scanned_items[barcode][0]
                scanned_items[barcode] = (existing_qty + qty, unit_str)
            else:
                scanned_items[barcode] = (qty, unit_str)
            
        return chain_name, scanned_items