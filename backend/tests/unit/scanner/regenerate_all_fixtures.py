"""
Regenerates raw text and expected JSON for ALL receipts in the receipts directory.
Uses ORIGINAL file names from the receipts subdirectories (digital/physical/complicated).
Groups multi-part receipts (e.g. mck3_1.jpg, mck3_2.jpg) into single test cases.
Bypasses test_recorder to preserve consistent naming.
"""
import os
import sys
import re
import json
import time
from pathlib import Path
from collections import defaultdict

# Ensure backend root is in python path
backend_path = str(Path(__file__).resolve().parent.parent.parent.parent)
sys.path.append(backend_path)

from src.infrastructure.scanner.scanner import scan_receipt, merge_receipts

RESULTS_DIR = Path(__file__).resolve().parent / "results"
RECEIPTS_DIR = RESULTS_DIR / "receipts"
RAW_DIR = RESULTS_DIR / "raw"
EXPECTED_DIR = RESULTS_DIR / "expected"


def collect_receipt_groups(target_category=None):
    """
    Scans all subdirectories under receipts/ and groups files by base name.
    Returns dict: { base_name: { "type": "pdf"|"image", "paths": [path1, ...] } }
    
    base_name comes directly from the receipt filename:
      - digital/mck1.pdf      => base_name = "mck1", type = "pdf"
      - physical/mck3_1.jpg   => base_name = "mck3", type = "image"  (grouped with mck3_2.jpg)
    """
    groups = {}
    
    categories = [target_category] if target_category else ["digital", "physical", "complicated"]
    
    for category in categories:
        cat_dir = RECEIPTS_DIR / category
        if not cat_dir.exists():
            continue
            
        files = sorted(os.listdir(cat_dir))
        
        # Group multi-part files
        file_groups = defaultdict(list)
        for f in files:
            match = re.match(r'^(.+?)(?:_(\d+))?\.(jpg|jpeg|png|pdf)$', f, re.IGNORECASE)
            if match:
                base_name = match.group(1)
                file_groups[base_name].append(str(cat_dir / f))
        
        for base_name, paths in file_groups.items():
            ext = os.path.splitext(paths[0])[-1].lower()
            source_type = "pdf" if ext == ".pdf" else "image"
            # Use base_name + source_type as key to avoid collisions
            # (e.g. mck1.pdf in digital vs mck1.jpg in physical)
            key = f"{base_name}_{source_type}"
            groups[key] = {
                "base_name": base_name,
                "type": source_type,
                "paths": sorted(paths),
                "category": category
            }
    
    return groups


def save_raw_text(base_name, source_type, slices_raw_texts):
    """Save combined raw text as plain readable text, using the original base_name."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    all_text_parts = []
    for raw_text in slices_raw_texts:
        try:
            parsed = json.loads(raw_text)
            if isinstance(parsed, list) and len(parsed) > 0 and isinstance(parsed[0], dict) and "text" in parsed[0]:
                plain_text = "\n".join(item["text"] for item in parsed)
            else:
                plain_text = raw_text
        except (json.JSONDecodeError, TypeError):
            plain_text = raw_text
        
        if plain_text:
            all_text_parts.append(plain_text)
    
    combined = "\n".join(all_text_parts)
    raw_path = RAW_DIR / f"{base_name}_{source_type}.txt"
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write(combined)


def save_expected_json(base_name, source_type, chain, final_data):
    """Save aggregated expected JSON, using the original base_name."""
    EXPECTED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Aggregate products by barcode
    aggregated = {}
    for product in final_data.get("products", []):
        bc = str(product.get("barcode", ""))
        if not bc:
            continue
        qty = float(product.get("quantity", 1.0))
        unit = product.get("unit", "UNIT")
        
        if bc in aggregated:
            aggregated[bc]["quantity"] += qty
        else:
            aggregated[bc] = {"barcode": bc, "quantity": qty, "unit": unit}
    
    expected = {
        "chain": chain,
        "items": list(aggregated.values())
    }
    
    expected_path = EXPECTED_DIR / f"{base_name}_{source_type}.json"
    with open(expected_path, "w", encoding="utf-8") as f:
        json.dump(expected, f, ensure_ascii=False, indent=4)


def main():
    target_category = sys.argv[1].lower() if len(sys.argv) > 1 else None
    valid_categories = ["digital", "physical", "complicated"]
    
    if target_category and target_category not in valid_categories:
        print(f"Error: Invalid category '{target_category}'. Valid options are: {', '.join(valid_categories)}")
        sys.exit(1)
        
    groups = collect_receipt_groups(target_category)
    
    print(f"Found {len(groups)} receipt groups across all categories:\n")
    for key, info in sorted(groups.items()):
        files_str = ", ".join([os.path.basename(p) for p in info["paths"]])
        print(f"  [{info['category']}] {key}: [{files_str}]")
    
    print(f"\n{'='*60}")
    print(f"Starting processing... (this will call Google Vision API)")
    print(f"{'='*60}\n")
    
    success = 0
    failed = 0
    
    for i, (key, info) in enumerate(sorted(groups.items())):
        base_name = info["base_name"]
        source_type = info["type"]
        paths = info["paths"]
        
        print(f"[{i+1}/{len(groups)}] {key} ...", end=" ", flush=True)
        
        try:
            # Scan each slice
            parsed_slices = []
            raw_texts = []
            
            for path in paths:
                result = scan_receipt(path)
                parsed_slices.append(result)
                raw_texts.append(result.get("raw_text", ""))
            
            # Merge if multiple parts
            if len(parsed_slices) > 1:
                final_data = merge_receipts(parsed_slices)
            else:
                final_data = parsed_slices[0]
            
            chain = final_data.get("chain", "Unknown")
            num_products = len(final_data.get("products", []))
            
            # Save with original name
            save_raw_text(base_name, source_type, raw_texts)
            save_expected_json(base_name, source_type, chain, final_data)
            
            print(f"OK (chain={chain}, products={num_products})")
            success += 1
            
        except Exception as e:
            print(f"FAILED: {e}")
            failed += 1
        
        # Small delay to avoid rate limiting
        if i < len(groups) - 1:
            time.sleep(0.5)
    
    print(f"\n{'='*60}")
    print(f"Done! Success: {success}, Failed: {failed}")
    print(f"Files saved to:")
    print(f"  Raw:      {RAW_DIR}")
    print(f"  Expected: {EXPECTED_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()