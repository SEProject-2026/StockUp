import os
import json
import pytest

from src.infrastructure.scanner.parsers.image_parser import parse_receipt_google
from src.infrastructure.scanner.parsers.pdf_parser import parse_receipt_pdf

FIXTURES_BASE = "tests/unit/scanner/results"

# Global list to hold data for the test report
TEST_RECORDS = []

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
    
    total_expected = len(exp_map)
    
    if total_expected == 0:
        if not act_map:
            return {
                "barcode_identification_rate": 100.0, 
                "quantity_accuracy_rate": 100.0, 
                "false_positives": 0, 
                "missing": [], 
                "extra": [], 
                "mismatched_qty": [],
                "expected_count": 0,
                "found_count": 0,
                "correct_qty_count": 0,
                "composite_score": 100.0
            }
        else:
            return {
                "barcode_identification_rate": 0.0, 
                "quantity_accuracy_rate": 0.0, 
                "false_positives": len(act_map), 
                "missing": [], 
                "extra": list(act_map.keys()), 
                "mismatched_qty": [],
                "expected_count": 0,
                "found_count": 0,
                "correct_qty_count": 0,
                "composite_score": 0.0
            }

    # 1. Barcode Identification (Discovery)
    missing_barcodes = [bc for bc in exp_map if bc not in act_map]
    found_count = total_expected - len(missing_barcodes)
    barcode_identification_rate = (found_count / total_expected) * 100

    # 2. Quantity Accuracy (Integrity)
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
        quantity_accuracy_rate = (correct_qty_count / found_count) * 100
    else:
        quantity_accuracy_rate = 0.0

    # 3. False Positives (Noise)
    extra_items = [bc for bc in act_map if bc not in exp_map]
    false_positives = len(extra_items)
    
    # Composite Score Formula
    # 70% weight for finding the barcode, 30% for getting quantity right.
    # Penalty: 20% penalty for every extra erroneous item relative to total items.
    base_score = (0.7 * barcode_identification_rate) + (0.3 * quantity_accuracy_rate)
    penalty = (false_positives / total_expected) * 100 * 0.20
    composite_score = max(0.0, base_score - penalty)
    
    return {
        "barcode_identification_rate": barcode_identification_rate,
        "quantity_accuracy_rate": quantity_accuracy_rate,
        "false_positives": false_positives,
        "missing": missing_barcodes,
        "extra": extra_items,
        "mismatched_qty": mismatched_qty,
        "expected_count": total_expected,
        "found_count": found_count,
        "correct_qty_count": correct_qty_count,
        "composite_score": composite_score
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

@pytest.fixture(scope="session", autouse=True)
def run_report_generator():
    # Setup: runs before all tests
    yield
    # Teardown: runs after all tests have finished
    if not TEST_RECORDS:
        return
        
    total_expected = 0
    total_found = 0
    total_correct_qty = 0
    total_false_positives = 0
    
    # Generate the string report
    report_lines = []
    report_lines.append("==== SCANNER ACCURACY REPORT ====\n")
    
    for rec in TEST_RECORDS:
        case_id = rec["case_id"]
        t = rec["source_type"]
        m = rec["metrics"]
        
        total_expected += m["expected_count"]
        total_found += m["found_count"]
        total_correct_qty += m["correct_qty_count"]
        total_false_positives += m["false_positives"]
        
        report_lines.append(f"Case: {case_id} ({t})")
        report_lines.append(f"  - Barcode Identification Rate: {m['barcode_identification_rate']:.1f}% ({m['found_count']}/{m['expected_count']})")
        report_lines.append(f"  - Quantity Accuracy Rate:    {m['quantity_accuracy_rate']:.1f}% ({m['correct_qty_count']}/{m['found_count']})")
        report_lines.append(f"  - False Positives (Noise):   {m['false_positives']}")
        report_lines.append(f"  >> COMPOSITE SCORE:          {m['composite_score']:.1f}/100")
        
        if m["missing"]: report_lines.append(f"    Missing: {m['missing']}")
        if m["extra"]: report_lines.append(f"    Extra (False Pos): {m['extra']}")
        if m["mismatched_qty"]:
            report_lines.append(f"    Mismatched QTY:")
            for item in m["mismatched_qty"]:
                report_lines.append(f"      [{item['barcode']}] Expected {item['expected']}, Got {item['actual']}")
        report_lines.append("-" * 40)
        
    # Global metrics
    report_lines.append("\n==== GLOBAL OVERALL RESULTS ====")
    if total_expected > 0:
        global_barcode_rate = (total_found / total_expected) * 100
        global_qty_rate = (total_correct_qty / total_found) * 100 if total_found > 0 else 0
        
        global_base = (0.7 * global_barcode_rate) + (0.3 * global_qty_rate)
        global_penalty = (total_false_positives / total_expected) * 100 * 0.20
        global_composite = max(0.0, global_base - global_penalty)
        
        report_lines.append(f"Total Expected Products: {total_expected}")
        report_lines.append(f"Global Barcode ID Rate:  {global_barcode_rate:.1f}% ({total_found}/{total_expected})")
        report_lines.append(f"Global QTY Acc. Rate:    {global_qty_rate:.1f}% ({total_correct_qty}/{total_found})")
        report_lines.append(f"Total False Positives:   {total_false_positives}")
        report_lines.append(f"OVERALL COMPOSITE SCORE: {global_composite:.1f}/100")
        report_lines.append("(Score weights: 70% Barcode Identification + 30% Quantity Accuracy - 20% penalty per mismatch ratio)")
    else:
        report_lines.append("No valid expectations found to calculate global rate.")
        
    report_text = "\n".join(report_lines)
    
    # Save to file
    report_path = os.path.join("tests", "unit", "scanner", "scanner_test_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)
        
    print(f"\n[INFO] Detailed scanner report saved to {report_path}")

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

    # Accumulate record for report
    TEST_RECORDS.append({
        "case_id": case_id,
        "source_type": source_type,
        "metrics": metrics
    })

    # Error Reporting in terminal
    if metrics["barcode_identification_rate"] < 100 or metrics["quantity_accuracy_rate"] < 100 or metrics["false_positives"] > 0:
        print(f"\n\n--- [FAILED/INCOMPLETE] {case_id} ({source_type}) ---")
        if metrics["missing"]: print(f"MISSING ITEMS: {metrics['missing']}")
        if metrics["extra"]: print(f"EXTRA ITEMS (Noise): {metrics['extra']}")
        if metrics["mismatched_qty"]:
            print("QUANTITY MISMATCHES (Post-Aggregation):")
            for item in metrics["mismatched_qty"]:
                print(f"  - Barcode {item['barcode']}: Expected {item['expected']}, Got {item['actual']}")
        print(f"Final Stats -> Barcode ID: {metrics['barcode_identification_rate']:.1f}% | Quantity Acc: {metrics['quantity_accuracy_rate']:.1f}% | Score: {metrics['composite_score']:.1f}")

    min_disc = 100.0 if source_type == "pdf" else 80.0
    min_int = 100.0 if source_type == "pdf" else 75.0

    assert metrics["barcode_identification_rate"] >= min_disc, f"Barcode ID Rate {metrics['barcode_identification_rate']}% below threshold"
    assert metrics["quantity_accuracy_rate"] >= min_int, f"Quantity Accuracy Rate {metrics['quantity_accuracy_rate']}% below threshold"