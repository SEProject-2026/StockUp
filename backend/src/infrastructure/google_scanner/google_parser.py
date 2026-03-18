import json
import re
from typing import Dict, List, Any


CHAIN_HPS = {
    "520038234": "shufersal",
    "520022732": "shufersal",
    "513770669": "ramilevi",
    "557756376": "ramilevi",
    "511956100": "yochananof",
    "511394112": "victory",
    "514068900": "victory",
    "514068980": "victory",
    "515163657": "mck",
    "512401618": "tivtaam",
    "510931484": "osherad",
    "511400265": "hazi-hinam",
}

def identify_chain(text: str) -> str:
    """Looks for a 9-digit company ID starting with 51 or 52."""
    hp_matches = re.findall(r'(?<!\d)(5[12]\d{7})(?!\d)', text)
    if hp_matches:
        for hp in hp_matches:
            if hp in CHAIN_HPS:
                return CHAIN_HPS[hp]
        return f"Unknown Chain (ID: {hp_matches[0]})"
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
    line_clean = re.sub(r'\b(?:2006|52149|1000150|6539930|8456129|6210717|17534|6321|74)\b', '', line_clean)
    line_clean = re.sub(r'\b\d+-\d+\b', '', line_clean)
    line_clean = re.sub(r'\b\d+/\d+(?:/\d+)?\b', '', line_clean)
    line_clean = re.sub(r'_(\d+)\b', r' \1', line_clean)
    return line_clean

def get_best_barcode(line_clean: str) -> str:
    # First, strip common weight/quantity descriptors so they aren't confused as barcodes
    # We restrict this to 1-4 digit numbers to avoid stripping valid 13-digit Israeli barcodes!
    units = r'(?:מל|מ"ל|מי"ל|גר|גרם|ק"ג|קג|L|ML|KG|%)'
    
    line_for_bcode = re.sub(rf'\b\d{{1,4}}(?:\.\d+)?\s*{units}\b', '', line_clean, flags=re.IGNORECASE)
    line_for_bcode = re.sub(rf'\b{units}\s*\d{{1,4}}(?:\.\d+)?\b', '', line_for_bcode, flags=re.IGNORECASE)
    # Also catch `ג 750` (which implies grams) while preserving `116 ג` (which implies 'Large')
    line_for_bcode = re.sub(r'\b[ג]\s*\d{1,4}(?:\.\d+)?\b', '', line_for_bcode, flags=re.IGNORECASE)

    # Israeli barcodes are typically 13 digits starting with 729
    israeli = re.findall(r'(729\d{10})', line_for_bcode)
    if israeli: 
        return max(israeli, key=len)
        
    normal = re.findall(r'(?<!\.)\b(\d{3,15})\b(?!\.)', line_for_bcode)
    prices = re.findall(r'\b\d+\.\d{2}\b', line_for_bcode)
    
    # Exclude parts of prices or obvious non-barcodes
    valid_normal = [n for n in normal if n not in prices and len(n) >= 3]
    
    if valid_normal:
        return max(valid_normal, key=len)
    return ""

def _extract_quantity_from_line(line: str) -> float | None:
    # Look for obvious weight (3 decimal places)
    match_3dec = re.search(r'\b(\d+\.\d{3})\b', line)
    if match_3dec:
        return float(match_3dec.group(1))

    # Look for explicit quantity followed by a multiplier symbol, matching missing right sides
    match_x = re.search(r'\b(\d+(?:\.\d+)?)\s*[:]?\s*[\*xXw](?![A-Za-zא-ת])', line)
    if match_x:
        return float(match_x.group(1))

    return None

def parse_receipt_google(text: str) -> Dict[str, Any]:
    """
    Parses a Google Vision receipt output, matching barcodes and handling line-by-line quantities.
    """
    chain = identify_chain(text)
    
    try:
        # Google Vision produces a JSON array of line objects
        lines_data = json.loads(text)
    except Exception:
        # Fallback if raw text
        lines_data = [{"text": line} for line in text.split("\n")]
        
    products = []
    current_barcode = None
    pending_barcode = None
    
    for row in lines_data:
        line_text = row.get("text", "")
        if not line_text.strip():
            continue
            
        if is_ignored_line(line_text):
            # Only explicitly clear states if it's a known payment/metadata keyword block.
            # Do NOT clear it just because a product description line has no numbers!
            payment_words = ["סה\"כ", "סה''כ", "תשלום", "אשראי", "עסקה", "חברה", "TOTAL", "Total"]
            if any(w in line_text for w in payment_words):
                current_barcode = None
                pending_barcode = None
            continue
            
        line_clean = clean_ocr_artifacts(line_text)
        bcode = get_best_barcode(line_clean)
        has_price = bool(re.search(r'\d+\.\d{2}', line_clean))
        is_discount = bool(re.search(r'-\d|\d-|\bהנחה\b|\bמוגבל\b|\bזיכוי\b|\bמבצע\b', line_clean))
        
        # If the line looks like a discount or reduction 
        if is_discount:
            # We skip it UNLESS it contains a full undeniable barcode (13 digits or 729...)
            if not bcode or (len(bcode) < 8 and not bcode.startswith('729')):
                continue
        
        if bcode:
            if has_price:
                # Complete line containing both a barcode and a price
                qty = _extract_quantity_from_line(line_clean) or 1.0
                products.append({"barcode": bcode, "quantity": qty})
                current_barcode = bcode
                pending_barcode = None
            else:
                # Candidate barcode, waiting for a price on subsequent lines
                pending_barcode = bcode
                
        else: # no barcode on this line
            if has_price:
                if pending_barcode:
                    # We found a price directly following a pending barcode!
                    qty = _extract_quantity_from_line(line_clean) or 1.0
                    products.append({"barcode": pending_barcode, "quantity": qty})
                    current_barcode = pending_barcode
                    pending_barcode = None
                else:
                    # Price line without any pending barcode.
                    # This could be a discount line, a total summary, or payment detail.
                    # OR it could be a weight/multiplier line containing a unit price (e.g., "6.90 * 0.435").
                    if current_barcode:
                        qty = _extract_quantity_from_line(line_clean)
                        if qty is not None and products[-1]["quantity"] == 1.0:
                            products[-1]["quantity"] = qty
                            current_barcode = None
            else:
                # No barcode, no price
                # Could be a wandering trailing quantity (e.g., "3 X" on its own line without a price)
                if current_barcode:
                    qty = _extract_quantity_from_line(line_clean)
                    if qty is not None:
                        # Only update if current quantity is exactly 1.0, 
                        # meaning we haven't already found the true weight/quantity yet.
                        if products[-1]["quantity"] == 1.0:
                            products[-1]["quantity"] = qty
                        # Clear active barcode so we don't accidentally apply more wandering quantities
                        current_barcode = None
                
    return {
        "chain": chain,
        "products": products
    }


