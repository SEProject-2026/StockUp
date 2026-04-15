import os
import shutil
import json
import re
from pathlib import Path

def save_receipt_test_case(chain_name: str, slices_info: list):
    """
    Saves multiple slices belonging to a single receipt scan.
    Generates informative base names (e.g., mck1, mck2_1, mck2_2).
    Converts raw text JSON array back into plain flat text.
    """
    try:
        base_dir = Path(__file__).resolve().parent
        results_dir = base_dir / "results"
        
        images_dir = results_dir / "images"
        raw_dir = results_dir / "raw"
        expected_dir = results_dir / "expected"
        
        images_dir.mkdir(parents=True, exist_ok=True)
        raw_dir.mkdir(parents=True, exist_ok=True)
        expected_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine base chain handle
        safe_chain = str(chain_name).lower().replace(" ", "")
        if safe_chain == "unknown" or not safe_chain:
            safe_chain = "unknown"
            
        # Find next available index for this chain
        max_id = 0
        pattern = re.compile(rf"^{re.escape(safe_chain)}(\d+)")
        if raw_dir.exists():
            for f in raw_dir.iterdir():
                match = pattern.match(f.name)
                if match:
                    val = int(match.group(1))
                    if val > max_id:
                        max_id = val
                        
        next_id = max_id + 1
        num_parts = len(slices_info)
        
        for idx, sinfo in enumerate(slices_info):
            image_path = sinfo.get("image_path")
            raw_text = sinfo.get("raw_text", "")
            result_data = sinfo.get("result", {})
            
            if not image_path or not os.path.exists(image_path):
                print(f"Warning: Image path does not exist: {image_path}")
                continue
                
            # Base naming logic
            if num_parts == 1:
                base_name = f"{safe_chain}{next_id}"
            else:
                base_name = f"{safe_chain}{next_id}_{idx+1}"
                
            ext = os.path.splitext(image_path)[-1].lower()
            file_suffix = "pdf" if ext == ".pdf" else "image"
            
            # 1. Save Image
            dest_img_path = images_dir / f"{base_name}{ext}"
            shutil.copy2(image_path, dest_img_path)
            
            # 2. Convert and Save Raw Text
            try:
                parsed_text = json.loads(raw_text)
                if isinstance(parsed_text, list) and len(parsed_text) > 0 and "text" in parsed_text[0]:
                    pure_text = "\n".join(item["text"] for item in parsed_text)
                else:
                    pure_text = raw_text
            except Exception:
                pure_text = raw_text
                
            raw_text_path = raw_dir / f"{base_name}_{file_suffix}.txt"
            with open(raw_text_path, "w", encoding="utf-8") as f:
                f.write(pure_text)
                
            # 3. Save Expected JSON
            # Aggregate products by barcode and sum quantities to match the expected test format
            aggregated_items = {}
            scanned_items = result_data.get("products", [])
            for product in scanned_items:
                bc = str(product.get("barcode", ""))
                if not bc:
                    continue
                    
                qty = float(product.get("quantity", 1.0))
                unit = product.get("unit", "UNIT")
                
                if bc in aggregated_items:
                    aggregated_items[bc]["quantity"] += qty
                else:
                    aggregated_items[bc] = {
                        "barcode": bc,
                        "quantity": qty,
                        "unit": unit
                    }
                    
            expected_items = list(aggregated_items.values())
                
            expected_data = {
                "chain": result_data.get("chain", safe_chain),
                "items": expected_items
            }
            
            expected_json_path = expected_dir / f"{base_name}_{file_suffix}.json"
            with open(expected_json_path, "w", encoding="utf-8") as f:
                json.dump(expected_data, f, ensure_ascii=False, indent=4)
                
            print(f"--- Test data successfully saved: {base_name}_{file_suffix} ---")
            
    except Exception as e:
        import traceback
        print(f"Failed to save receipt test cases: {e}\n{traceback.format_exc()}")
