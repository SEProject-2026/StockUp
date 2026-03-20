import json
import re
import os
from typing import List, Dict, Any, Optional

def _normalize_unit(unit: str) -> str:
    unit = unit.replace('"', '').replace("'", "").strip().lower()
    if any(u in unit for u in ['גק', 'קג', 'קיג', 'ג"ק', 'ק"ג']):
        return "KG"
    return "UNIT"

def _extract_pdf_line_data(line: str, index: int, trace: List[str]) -> Optional[Dict[str, Any]]:
    #remove discount lines
    promo_keywords = ['מבצע:', ':מבצע', ':עצבמ','חולשמ']
    if any(kw in line for kw in promo_keywords):
        trace.append(f"L{index}: REJECTED - Promotion/Discount line detected: '{line[:30]}...'")
        return None
    
    units_pattern = r'(\'יח|יח\'|חי|יח|יחידה|יחידות|ק"ג|ג"ק|קג|גק|קיג|ג"ק|`חי|`ח י|י ח|י\"ח|ח\"י)'
    unit_match = re.search(units_pattern, line)
    
    
    if not unit_match:
        if re.search(r'\d{5,}', line):
            trace.append(f"L{index}: REJECTED - Found long number but no unit anchor in: '{line[:40]}...'")
        return None

    unit_str = unit_match.group(0)
    unit_start = unit_match.start()
    unit_end = unit_match.end()

    # 2. extract qty next to unit - look both before and after the unit for a number (allowing for formats like "2.5" or "3")
    before_segment = line[max(0, unit_start-15):unit_start].strip()
    after_segment = line[unit_end:unit_end+15].strip()
    
    qty_match = None
    before_nums = re.findall(r'(\d+\.\d{1,3}|\d+)', before_segment)
    after_nums = re.findall(r'(\d+\.\d{1,3}|\d+)', after_segment)

    if before_nums:
        qty_match = before_nums[-1]
    elif after_nums:
        qty_match = after_nums[0]

    if not qty_match:
        trace.append(f"L{index}: REJECTED - Found unit '{unit_str}' but no numeric quantity nearby")
        return None

    # 3. extract barcode - the longest number that remains
    # temporarily remove the quantity and unit and clean prices (format x.xx)
    temp_line = line.replace(qty_match, ' ', 1).replace(unit_str, ' ', 1)
    temp_line = re.sub(r'\b\d+\.\d{2}\b', ' ', temp_line)
    
    barcodes = re.findall(r'\b\d{3,14}\b', temp_line)
    if not barcodes:
        trace.append(f"L{index}: REJECTED - Found unit/qty but no barcode candidate (3-14 digits) in: '{line[:40]}...'")
        return None
    
    barcode = max(barcodes, key=len)

    # 4. final sanity checks
    if len(barcode) < 3:
        trace.append(f"L{index}: REJECTED - Barcode '{barcode}' is too short")
        return None

    try:
        qty_val = float(qty_match)
        if qty_val <= 0:
            trace.append(f"L{index}: INFO - Quantity was {qty_match}, skipped")
            return None
        
        trace.append(f"L{index}: SUCCESS - ID {barcode} | Qty {qty_val} | Unit {unit_str}")
        return {
            "barcode": barcode,
            "quantity": int(qty_val) if qty_val.is_integer() else qty_val,
            "unit": _normalize_unit(unit_str)
        }
    except Exception as e:
        trace.append(f"L{index}: ERROR - Exception during parsing: {str(e)}")
        return None

def parse_receipt_pdf(text: str, chain: str) -> Dict[str, Any]:
    try:
        raw_data = json.loads(text)
        lines = [row.get("text", "") for row in raw_data]
    except (json.JSONDecodeError, TypeError):
        lines = [line for line in text.split('\n')]
    products_map = {}
    decision_log = ["=== Comprehensive PDF Parsing Log ==="]

    for i, line in enumerate(lines):
        clean_line = line.strip()
        if not clean_line:
            decision_log.append(f"L{i}: IGNORED - Empty line")
            continue

        metadata_keywords = ["סה\"כ", "סה''כ", "טלפון", "פקס", "כתובת", "עוסק", "עמוד", "תאריך", "מ\"עמ"]
        if any(kw in clean_line for kw in metadata_keywords):
            decision_log.append(f"L{i}: SKIP - Metadata/Summary detected: '{clean_line[:30]}...'")
            continue
            
        line_trace = []
        product = _extract_pdf_line_data(clean_line, i, line_trace)
        
        if product:
            bcode = product['barcode']
            if bcode in products_map:
                old_qty = products_map[bcode]['quantity']
                products_map[bcode]['quantity'] += product['quantity']
                decision_log.append(f"L{i}: SUMMED - Added {product['quantity']} to {old_qty} for ID {bcode}")
            else:
                products_map[bcode] = product
                decision_log.append(line_trace[0])
        else:
            if line_trace:
                decision_log.extend(line_trace)
            else:
                decision_log.append(f"L{i}: IGNORED - No identifying features found")

    _write_pdf_debug_log(decision_log)
    
    return {"chain": chain, "products": list(products_map.values())}

def _write_pdf_debug_log(logs: List[str]):
    debug_dir = os.path.join(os.getcwd(), "debug")
    os.makedirs(debug_dir, exist_ok=True)
    with open(os.path.join(debug_dir, "pdf_parsing_decisions.log"), "w", encoding="utf-8") as f:
        f.write("\n".join(logs))