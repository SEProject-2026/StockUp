import os
import json
import pytest

from src.infrastructure.scanner.parsers.image_parser import parse_receipt_google
from src.infrastructure.scanner.parsers.pdf_parser import parse_receipt_pdf

FIXTURES_BASE = "tests/unit/scanner/results"

def aggregate_products(products):
    """
    Groups products by barcode and sums their quantities.
    """
    aggregated = {}
    for p in products:
        bc = str(p.get("barcode", ""))
        if not bc:
            continue
        
        qty = float(p.get("quantity", 0))
        
        if bc in aggregated:
            aggregated[bc]["quantity"] += qty
        else:
            # Create a copy to avoid mutating the original parser output
            aggregated[bc] = p.copy()
            aggregated[bc]["quantity"] = qty
            
    return list(aggregated.values())

def calculate_metrics(actual_products, expected_items, qty_tolerance=0.1):
    # Sum identical barcodes in the actual results before comparing
    actual_aggregated = aggregate_products(actual_products)
    
    exp_map = {str(item["barcode"]): item for item in expected_items}
    act_map = {str(item["barcode"]): item for item in actual_aggregated}
    
    if not exp_map:
        if not act_map:
            return {"discovery": 100.0, "integrity": 100.0, "noise": 0, "missing": [], "extra": [], "mismatched_qty": []}
        else:
            return {"discovery": 0.0, "integrity": 0.0, "noise": len(act_map), "missing": [], "extra": list(act_map.keys()), "mismatched_qty": []}

    # 1. Discovery
    missing_barcodes = [bc for bc in exp_map if bc not in act_map]
    found_count = len(exp_map) - len(missing_barcodes)
    discovery_rate = (found_count / len(exp_map)) * 100

    # 2. Integrity (Quantity comparison)
    correct_qty_count = 0
    mismatched_qty = []
    
    if found_count > 0:
        for bc, exp in exp_map.items():
            if bc in act_map:
                act_qty = float(act_map[bc].get("quantity", 0))
                exp_qty = float(exp.get("quantity", 0))
                if abs(act_qty - exp_qty) <= qty_tolerance:
                    correct_qty_count += 1
                else:
                    mismatched_qty.append({
                        "barcode": bc,
                        "expected": exp_qty,
                        "actual": act_qty
                    })
        integrity_rate = (correct_qty_count / found_count) * 100
    else:
        integrity_rate = 0.0

    extra_items = [bc for bc in act_map if bc not in exp_map]
    
    return {
        "discovery": discovery_rate,
        "integrity": integrity_rate,
        "noise": len(extra_items),
        "missing": missing_barcodes,
        "extra": extra_items,
        "mismatched_qty": mismatched_qty
    }

def get_test_cases():
    cases = []
    raw_dir = os.path.join(FIXTURES_BASE, "raw")
    if not os.path.exists(raw_dir): return []
    for filename in os.listdir(raw_dir):
        if filename.endswith("_pdf.txt"):
            cases.append((filename.replace("_pdf.txt", ""), "pdf", filename))
        elif filename.endswith("_image.txt"):
            cases.append((filename.replace("_image.txt", ""), "image", filename))
    return cases

@pytest.mark.parametrize("case_id, source_type, raw_filename", get_test_cases())
def test_parsers_accuracy(case_id, source_type, raw_filename):
    suffix = "_pdf.json" if source_type == "pdf" else "_image.json"
    exp_path = os.path.join(FIXTURES_BASE, "expected", f"{case_id}{suffix}")
    if not os.path.exists(exp_path): pytest.skip(f"Missing JSON: {exp_path}")
    
    with open(exp_path, 'r', encoding='utf-8') as f:
        expected = json.load(f)
    with open(os.path.join(FIXTURES_BASE, "raw", raw_filename), 'r', encoding='utf-8') as f:
        raw_content = f.read()

    if source_type == "pdf":
        actual = parse_receipt_pdf(raw_content, chain=expected["chain"])
        metrics = calculate_metrics(actual["products"], expected["items"], qty_tolerance=0.0)
    else:
        actual = parse_receipt_google(raw_content)
        metrics = calculate_metrics(actual["products"], expected["items"], qty_tolerance=0.1)

    # Error Reporting
    if metrics["discovery"] < 100 or metrics["integrity"] < 100 or metrics["noise"] > 0:
        print(f"\n\n--- [FAILED/INCOMPLETE] {case_id} ({source_type}) ---")
        if metrics["missing"]: print(f"MISSING ITEMS: {metrics['missing']}")
        if metrics["extra"]: print(f"EXTRA ITEMS (Noise): {metrics['extra']}")
        if metrics["mismatched_qty"]:
            print("QUANTITY MISMATCHES (Post-Aggregation):")
            for item in metrics["mismatched_qty"]:
                print(f"  - Barcode {item['barcode']}: Expected {item['expected']}, Got {item['actual']}")
        print(f"Final Stats -> Discovery: {metrics['discovery']:.1f}% | Integrity: {metrics['integrity']:.1f}%")

    min_disc = 100.0 if source_type == "pdf" else 80.0
    min_int = 100.0 if source_type == "pdf" else 75.0

    assert metrics["discovery"] >= min_disc
    assert metrics["integrity"] >= min_int