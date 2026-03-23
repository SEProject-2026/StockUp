import json
import os
import re
from typing import Dict, List, Any, Optional, Union

from numpy import trace

ENABLE_DEBUG = os.environ.get("ENABLE_DEBUG", "False").lower() == "true"

CHAIN_HPS = {
    "520038234": "shufersal",
    "520022732": "shufersal",
    "513770669": "ramilevi",
    "557756376": "ramilevi",
    "511344186": "yohananof",
    "511394112": "victory",
    "514068900": "victory",
    "514068980": "victory",
    "515163657": "mck",
    "512792714": "tivtaam",
    "510931484": "osherad",
    "511400265": "hazi-hinam",
}

def identify_chain(text: str) -> str:
    """Looks for a 9-digit company ID starting with 51 or 52, with a fallback to raw text matching."""
    hp_matches = re.findall(r'(?<!\d)(5[12]\d{7})(?!\d)', text)
    if hp_matches:
        for hp in hp_matches:
            if hp in CHAIN_HPS:
                return CHAIN_HPS[hp]
                
    # Fallback to pure text match if no valid HP is found or matched
    chain_names = {
        "רמי לוי": "ramilevi",
        "שופרסל": "shufersal",
        "מחסני השוק": "mck",
        "אושר עד": "osherad",
        "יוחננוף": "yohananof",
        "טיב טעם": "tivtaam",
        "ויקטורי": "victory",
        "חצי חינם": "hazi-hinam"
    }
    
    for heb_name, eng_id in chain_names.items():
        if heb_name in text:
            return eng_id
            
    return "Unknown Chain"

def is_ignored_line(line: str) -> bool:
    """Check if the line is a summary, metadata, or masked credit card line."""
    ignore_words = [
        "סה\"כ", "סה''כ", "כ\"הס", "כ''הס", "לתשלום", "עודף", "אשראי", "מזומן", 
        "לקוח", "חוקל", "דלפק", "קפלד", "טלפון", "ןופלט", "ת.ז", "ז.ת", "ת.ד", 
        "ד.ת", "פקס", "סקפ", "קתי", "קתעה", "ש.ת", " CN ", " IL ", " ILS ", 
        "סה כ", "TOTAL", "Total", "total", "PAY", "Pay", "pay", "תשלום", "סיכום", 
        "פריטים", "xALx", "Ltc4", "ALLG", "nwx", "OLZO"
    ]
    if any(word in line for word in ignore_words):
        return True
    if re.search(r'[\*xX]{3,}', line):
        return True
    if not re.search(r'\d', line):
        return True
    return False

def clean_ocr_artifacts(line: str) -> str:
    """Removes dates, times, phone numbers, and known non-product IDs from the text."""
    line_clean = re.sub(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', '', line)
    line_clean = re.sub(r'\b\d{1,2}:\d{2}(?::\d{2})?\b', '', line_clean)
    line_clean = re.sub(r'\b0\d{1,2}-?\d{7}\b', '', line_clean)
    line_clean = re.sub(r'\b1\d{3}-\d{3}-\d{3}\b', '', line_clean)
    line_clean = re.sub(r'\b5[12]\d{7}\b', '', line_clean)
    line_clean = re.sub(r'\b\d+-\d+\b', '', line_clean)
    line_clean = re.sub(r'\b\d+/\d+(?:/\d+)?\b', '', line_clean)
    line_clean = re.sub(r'_(\d+)\b', r' \1', line_clean)
    return line_clean

def get_best_barcode(line_clean: str, trace: Optional[List[str]] = None) -> str:
    """Finds the most likely barcode and logs why others were skipped."""
    units = r'(?:מל|מ"ל|מי"ל|גר|גרם|ק"ג|קג|L|ML|KG|%)'
    
    # Cleaning descriptors for barcode search
    line_for_bcode = re.sub(rf'\b\d{{1,4}}(?:\.\d+)?\s*{units}\b', '', line_clean, flags=re.IGNORECASE)
    line_for_bcode = re.sub(rf'\b{units}\s*\d{{1,4}}(?:\.\d+)?\b', '', line_for_bcode, flags=re.IGNORECASE)
    line_for_bcode = re.sub(r'\b[ג]\s*\d{1,4}(?:\.\d+)?\b', '', line_for_bcode, flags=re.IGNORECASE)

    # 1. Look for Israeli 729 barcodes
    israeli = re.findall(r'(729\d{10})', line_for_bcode)
    if israeli:
        bcode = max(israeli, key=len)
        if trace is not None: trace.append(f"Selected high-priority Israeli barcode: {bcode}")
        return bcode
        
    # 2. General numbers
    normal = re.findall(r'(?<!\.)\b(\d{3,15})\b(?!\.)', line_for_bcode)
    prices = re.findall(r'\b\d+\.\d{2}\b', line_for_bcode)
    
    valid_normal = [n for n in normal if n not in prices and len(n) >= 3]
    
    if valid_normal:
        bcode = max(valid_normal, key=len)
        if trace is not None:
            skipped = [n for n in normal if n != bcode]
            if skipped: trace.append(f"Selected barcode {bcode}. Skipped potential candidates: {skipped}")
            else: trace.append(f"Selected lone barcode candidate: {bcode}")
        return bcode

    if trace is not None and normal:
        trace.append(f"Numbers found but rejected as barcodes (likely prices or too short): {normal}")
    return ""

def _extract_quantity_from_line(line: str, trace: Optional[List[str]] = None) -> Optional[Union[float, int]]:
    """Strictly extracts quantity with multiplier logic and logs decision steps."""
    def is_price_format(val_str: str) -> bool:
        if '.' in val_str:
            parts = val_str.split('.')
            return len(parts[1]) == 2
        return False

    def cast_to_numeric(val_str: str) -> Optional[Union[float, int]]:
        try:
            f_val = float(val_str)
            return int(f_val) if f_val.is_integer() else f_val
        except ValueError: return None

    #Absolute Priority: High-precision weight (x.xxx)
    #If this format exists, we assume it's a weight regardless of other symbols
    weight_match = re.search(r'\b\d{1,2}\.\d{3}\b', line)
    if weight_match:
        val_str = weight_match.group(0)
        if float(val_str) < 20.000:  # Sanity check to avoid misinterpreting prices as weights
            if trace is not None:
                trace.append(f"High-precision weight detected (x.xxx): {val_str}. Returning immediately.")
            return float(val_str)
    
    # Multiplier detection
    mult_match = re.search(r'(\d+(?:\.\d+)?)\s*[\*xX×]\s*(\d+(?:\.\d+)?)', line)
    if mult_match:
        side_a, side_b = mult_match.group(1), mult_match.group(2)
        val_a, val_b = cast_to_numeric(side_a), cast_to_numeric(side_b)
        
        if trace is not None: trace.append(f"Multiplier pattern detected: {side_a} and {side_b}")

        if is_price_format(side_a) and not is_price_format(side_b):
            if trace is not None: trace.append(f"Selecting {side_b} (quantity) over {side_a} (price format)")
            return val_b
        if is_price_format(side_b) and not is_price_format(side_a):
            if trace is not None: trace.append(f"Selecting {side_a} (quantity) over {side_b} (price format)")
            return val_a
            
        # Weight precision logic (x.xxx)
        if '.' in side_a and len(side_a.split('.')[1]) == 3:
            if trace is not None: trace.append(f"Selecting {side_a} as high-precision weight (x.xxx)")
            return val_a
        
        if trace is not None: trace.append(f"Defaulting to integer/second value: {val_b}")
        return val_b if isinstance(val_b, int) else val_a

    # Single-sided multiplier
    single_mult = re.search(r'\b(\d+(?:\.\d+)?)\s*[\*xX×]', line)
    if single_mult:
        val_str = single_mult.group(1)
        if not is_price_format(val_str):
            if trace is not None: trace.append(f"Single multiplier found: Using {val_str}")
            return cast_to_numeric(val_str)
        elif trace is not None:
            trace.append(f"Single multiplier found but {val_str} is in price format. Skipping.")

    return None


def is_end_of_receipt(line: str) -> bool:
    """Checks if the line contains a keyword indicating the end of the receipt footprint."""
    end_words = ["אמצעי", "ישרכארט", "כאל", "כ.אשראי", "ויזה", "ישראכרט"]
    return any(word in line for word in end_words)

def parse_receipt_google(text: str) -> Dict[str, Any]:
    """Parses receipt and writes a 'parsing_decisions.log' to the debug folder."""
    chain = identify_chain(text)
    decision_log = [f"=== Receipt Parse Start | Chain: {chain} ==="]
    
    try:
        lines_data = json.loads(text)
    except Exception:
        lines_data = [{"text": line} for line in text.split("\n")]
        
    products = []
    current_barcode = None
    pending_barcode = None
    
    for index, row in enumerate(lines_data):
        line_text = row.get("text", "")
        if not line_text.strip(): continue
        
        line_trace = []
        
        if is_end_of_receipt(line_text):
            decision_log.append(f"Line {index}: '{line_text}' -> END OF RECEIPT DETECTED.")
            break
            
        if is_ignored_line(line_text):
            decision_log.append(f"Line {index}: '{line_text}' -> IGNORED (Metadata/Summary)")
            if any(w in line_text for w in ["סה\"כ", "תשלום", "TOTAL"]):
                current_barcode = pending_barcode = None
            continue
            
        line_clean = clean_ocr_artifacts(line_text)
        bcode = get_best_barcode(line_clean, trace=line_trace)
        qty_from_line = _extract_quantity_from_line(line_clean, trace=line_trace)
        has_price = bool(re.search(r'(?<!-)\b\d+\.\d{2}\b(?!-)', line_clean))
        is_discount = bool(re.search(r'-\d|\d-|\bהנחה\b|\bמבצע\b', line_clean))
        
        # State tracking for logging
        current_action = "Processing"

        if is_discount:
            current_action = "Discount Logic"
            if current_barcode and qty_from_line is not None:
                if products[-1]["quantity"] == 1.0:
                    line_trace.append(f"Updated quantity for product {current_barcode} using discount line data.")
                    products[-1]["quantity"] = qty_from_line
            if not bcode or (len(bcode) < 8 and not bcode.startswith('729')):
                decision_log.append(f"Line {index}: '{line_text}' [{current_action}]\n    -> " + "\n    -> ".join(line_trace))
                continue

        if bcode:
            qty = qty_from_line or 1.0
            if has_price:
                products.append({"barcode": bcode, "quantity": qty})
                current_barcode, pending_barcode = bcode, None
                line_trace.append(f"Committed product: {bcode} (qty: {qty})")
            else:
                pending_barcode = bcode
                line_trace.append(f"Pending price for barcode: {bcode}")
        else:
            if has_price:
                if pending_barcode:
                    qty = qty_from_line or 1.0
                    products.append({"barcode": pending_barcode, "quantity": qty})
                    line_trace.append(f"Price found. Committed pending product: {pending_barcode} (qty: {qty})")
                    current_barcode, pending_barcode = pending_barcode, None
                elif current_barcode and qty_from_line is not None:
                    if products[-1]["quantity"] == 1.0:
                        line_trace.append(f"Late quantity found. Updating {current_barcode}.")
                        products[-1]["quantity"] = qty_from_line
                        current_barcode = None
            elif current_barcode and qty_from_line is not None:
                if products[-1]["quantity"] == 1.0:
                    line_trace.append(f"Late standalone quantity found for {current_barcode}.")
                    products[-1]["quantity"] = qty_from_line
                current_barcode = None
        # Add line data to master log
        log_entry = f"Line {index}: '{line_text}' [{current_action}]"
        if line_trace:
            log_entry += "\n    -> " + "\n    -> ".join(line_trace)
        decision_log.append(log_entry)
    for product in products:
        qty = product["quantity"]
        product["unit"] = "UNIT" if isinstance(qty, int) or qty.is_integer() else "KG"

    # Save to debug folder
    _write_debug_log(decision_log)
    return {"chain": chain, "products": products}

def _write_debug_log(logs: List[str]) -> None:
    if not ENABLE_DEBUG:
        return
    debug_dir = os.path.join(os.getcwd(), "debug")
    if not os.path.exists(debug_dir): os.makedirs(debug_dir)
    with open(os.path.join(debug_dir, "parsing_decisions.log"), "w", encoding="utf-8") as f:
        f.write("\n\n".join(logs))

        

