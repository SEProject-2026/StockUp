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

def determine_category_and_files(case_id, source_type):
    receipts_dir = os.path.join(FIXTURES_BASE, "receipts")
    if not os.path.exists(receipts_dir):
        return "General", 0
    
    # 1. Search in subdirectories
    for category in ["digital", "physical", "complicated"]:
        cat_dir = os.path.join(receipts_dir, category)
        if os.path.exists(cat_dir):
            file_count = 0
            found = False
            for f in os.listdir(cat_dir):
                if f.startswith(case_id):
                    remainder = f[len(case_id):]
                    if remainder.startswith('.') or remainder.startswith('_'):
                        is_pdf = f.lower().endswith('.pdf')
                        if source_type == "pdf" and is_pdf:
                            found = True
                            file_count += 1
                        elif source_type == "image" and not is_pdf:
                            found = True
                            file_count += 1
            if found:
                return category, file_count

    # 2. Search in root if not in subdirectories (General category)
    file_count = 0
    if os.path.exists(receipts_dir):
        for f in os.listdir(receipts_dir):
            file_path = os.path.join(receipts_dir, f)
            if os.path.isfile(file_path):
                if f.startswith(case_id):
                    remainder = f[len(case_id):]
                    if remainder.startswith('.') or remainder.startswith('_'):
                        is_pdf = f.lower().endswith('.pdf')
                        if source_type == "pdf" and is_pdf:
                            file_count += 1
                        elif source_type == "image" and not is_pdf:
                            file_count += 1
    
    return "General", file_count

def get_test_cases():
    cases = []
    raw_dir = os.path.join(FIXTURES_BASE, "raw")
    if not os.path.exists(raw_dir): return []
    
    for filename in os.listdir(raw_dir):
        if filename.endswith("_pdf.txt"):
            case_id = filename.replace("_pdf.txt", "")
            cat, media_count = determine_category_and_files(case_id, "pdf")
            cases.append((case_id, "pdf", cat, media_count, filename))
        elif filename.endswith("_image.txt"):
            case_id = filename.replace("_image.txt", "")
            cat, media_count = determine_category_and_files(case_id, "image")
            cases.append((case_id, "image", cat, media_count, filename))
            
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
    
    category_metrics = {}
    
    # Generate the string report
    report_lines = []
    report_lines.append("==== SCANNER ACCURACY REPORT ====\n")
    
    for rec in TEST_RECORDS:
        case_id = rec["case_id"]
        t = rec["source_type"]
        cat = rec["category"]
        media_count = rec["media_count"]
        m = rec["metrics"]
        
        # Accumulate category metrics
        if cat not in category_metrics:
            category_metrics[cat] = {
                "expected": 0, "found": 0, "correct_qty": 0, "false_positives": 0, "receipt_count": 0, "media_count": 0
            }
        category_metrics[cat]["expected"] += m["expected_count"]
        category_metrics[cat]["found"] += m["found_count"]
        category_metrics[cat]["correct_qty"] += m["correct_qty_count"]
        category_metrics[cat]["false_positives"] += m["false_positives"]
        category_metrics[cat]["receipt_count"] += 1
        category_metrics[cat]["media_count"] += media_count
        
        # Accumulate global metrics
        total_expected += m["expected_count"]
        total_found += m["found_count"]
        total_correct_qty += m["correct_qty_count"]
        total_false_positives += m["false_positives"]
        
        report_lines.append(f"Case: {case_id} ({t}) [Category: {cat.capitalize()}]")
        report_lines.append(f"  - Barcode ID Rate:           {m['barcode_identification_rate']:.1f}% ({m['found_count']}/{m['expected_count']})")
        report_lines.append(f"  - Quantity Accuracy Rate:    {m['quantity_accuracy_rate']:.1f}% ({m['correct_qty_count']}/{m['found_count'] if m['found_count'] > 0 else 0})")
        report_lines.append(f"  - False Positives (Noise):   {m['false_positives']}")
        report_lines.append(f"  >> COMPOSITE SCORE:          {m['composite_score']:.1f}/100")
        
        if m["missing"]: report_lines.append(f"    Missing: {m['missing']}")
        if m["extra"]: report_lines.append(f"    Extra (False Pos): {m['extra']}")
        if m["mismatched_qty"]:
            report_lines.append(f"    Mismatched QTY:")
            for item in m["mismatched_qty"]:
                report_lines.append(f"      [{item['barcode']}] Expected {item['expected']}, Got {item['actual']}")
        report_lines.append("-" * 40)
        
    report_lines.append("\n==== CATEGORY RESULTS ====")
    for cat, metrics in category_metrics.items():
        cat_expected = metrics["expected"]
        cat_found = metrics["found"]
        cat_correct_qty = metrics["correct_qty"]
        cat_false_positives = metrics["false_positives"]
        cat_receipt_count = metrics["receipt_count"]
        cat_media_count = metrics["media_count"]
        
        if cat_expected > 0:
            cat_barcode_rate = (cat_found / cat_expected) * 100
            cat_qty_rate = (cat_correct_qty / cat_found) * 100 if cat_found > 0 else 0
            cat_base = (0.7 * cat_barcode_rate) + (0.3 * cat_qty_rate)
            cat_penalty = (cat_false_positives / cat_expected) * 100 * 0.20
            cat_composite = max(0.0, cat_base - cat_penalty)
            
            report_lines.append(f"Category: {cat.capitalize()}")
            report_lines.append(f"  - Total Receipts:    {cat_receipt_count} (Total Files: {cat_media_count})")
            report_lines.append(f"  - Expected Products: {cat_expected}")
            report_lines.append(f"  - Barcode ID Rate:   {cat_barcode_rate:.1f}% ({cat_found}/{cat_expected})")
            report_lines.append(f"  - QTY Acc. Rate:     {cat_qty_rate:.1f}% ({cat_correct_qty}/{cat_found})")
            report_lines.append(f"  - False Positives:   {cat_false_positives}")
            report_lines.append(f"  >> CATEGORY SCORE:   {cat_composite:.1f}/100")
            report_lines.append("-" * 40)
        else:
             report_lines.append(f"Category: {cat.capitalize()} (No valid expectations)")
             report_lines.append(f"  - Total Receipts: {cat_receipt_count} (Total Files: {cat_media_count})")
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

@pytest.mark.parametrize("case_id, source_type, category, media_count, raw_filename", get_test_cases())
def test_parsers_accuracy(case_id, source_type, category, media_count, raw_filename):
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
        "category": category,
        "media_count": media_count,
        "metrics": metrics
    })

    # Error Reporting in terminal
    if metrics["barcode_identification_rate"] < 100 or metrics["quantity_accuracy_rate"] < 100 or metrics["false_positives"] > 0:
        print(f"\n\n--- [FAILED/INCOMPLETE] {case_id} ({source_type}) [{category.capitalize()}] ---")
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