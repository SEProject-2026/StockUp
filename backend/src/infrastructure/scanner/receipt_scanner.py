import json
import os

from src.infrastructure.scanner.scanner import scan_receipt, merge_receipts

ENABLE_DEBUG = os.environ.get("ENABLE_DEBUG", "False").lower() == "true"

class ReceiptScanner:

    def _save_scan_debug_json(self, image_paths: list, chain_name: str, scanned_items: dict):
        """
        Saves the final scan result to a JSON file for testing and validation.
        """
        if not ENABLE_DEBUG:
            return
        try:
            results_dir = os.path.join(os.getcwd(), "results", "expected")
            os.makedirs(results_dir, exist_ok=True)

            # Create a filename based on the first image processed
            base_name = os.path.splitext(os.path.basename(image_paths[0]))[0]
            debug_file_path = os.path.join(results_dir, f"{base_name}_final_result.json")

            # Structure the data for easy testing
            debug_data = {
                "chain": chain_name,
                "items": [
                    {
                        "barcode": barcode,
                        "quantity": data[0],
                        "unit": data[1]
                    }
                    for barcode, data in scanned_items.items()
                ]
            }

            with open(debug_file_path, "w", encoding="utf-8") as f:
                json.dump(debug_data, f, ensure_ascii=False, indent=4)
            
            print(f"--- Scan Result JSON saved to: {debug_file_path} ---")
        except Exception as e:
            # Using print or a fallback logger if app_logger isn't imported here
            print(f"Warning: Failed to save scan debug JSON: {e}")
    def parse_receipt(self,all_paths: list) -> tuple[str, dict]:
        """
        Parses one or more receipt images and merges them.
        """
        # Scan all slices
        parsed_slices = []
        slices_info = []
        
        for path in all_paths:
            # Using the core function from your scanner.py
            result = scan_receipt(path)
            parsed_slices.append(result)
            
            raw_text = result.get("raw_text", "")
            slices_info.append({
                "image_path": path,
                "raw_text": raw_text,
                "result": result
            })
            
        # Merge if there are multiple parts (Panorama Stitching)
        if len(parsed_slices) > 1:
            final_data = merge_receipts(parsed_slices)
        else:
            final_data = parsed_slices[0]
            
        # The service expects (chain_name, items_dict)
        chain_name = final_data.get("chain", "Unknown")
        
        if ENABLE_DEBUG:
            try:
                import sys
                from pathlib import Path
                backend_path = str(Path(__file__).resolve().parent.parent.parent.parent.parent)
                if backend_path not in sys.path:
                    sys.path.append(backend_path)
                
                from tests.unit.scanner.test_recorder import save_receipt_test_case
                save_receipt_test_case(chain_name, slices_info)
            except Exception as e:
                print(f"Warning: Failed to execute test case recorder: {e}")
                
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
        
        self._save_scan_debug_json(all_paths, chain_name, scanned_items)

        return chain_name, scanned_items