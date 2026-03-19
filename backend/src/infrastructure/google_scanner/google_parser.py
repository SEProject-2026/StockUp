import json
import re
from typing import Dict, List, Any, Optional, Union


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
        "יוחננוף": "yochananof",
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

def _extract_quantity_from_line(line: str) -> Optional[Union[float, int]]:
    """
    Strictly extracts quantity ONLY when associated with a multiplier symbol (*, x, X, ×).
    This prevents product descriptions (like '40 gram') from being misidentified as quantities.
    """
    
    def is_price_format(val_str: str) -> bool:
        """Checks if a numeric string follows the currency/price format (x.xx)."""
        if '.' in val_str:
            parts = val_str.split('.')
            return len(parts[1]) == 2
        return False

    def cast_to_numeric(val_str: str) -> Optional[Union[float, int]]:
        """Converts string to the most appropriate numeric type."""
        try:
            f_val = float(val_str)
            return int(f_val) if f_val.is_integer() else f_val
        except ValueError:
            return None

    # 1. Multiplier detection (Checking both sides of the symbol)
    # Pattern: [Number] [Symbol] [Number]
    mult_match = re.search(r'(\d+(?:\.\d+)?)\s*[\*xX×]\s*(\d+(?:\.\d+)?)', line)
    if mult_match:
        side_a, side_b = mult_match.group(1), mult_match.group(2)
        val_a = cast_to_numeric(side_a)
        val_b = cast_to_numeric(side_b)
        
        # Priority: If one side is a price (x.xx) and the other is not, take the other
        if is_price_format(side_a) and not is_price_format(side_b):
            return val_b
        if is_price_format(side_b) and not is_price_format(side_a):
            return val_a
            
        # Fallback for weighted items (x.xxx) or integers
        if '.' in side_a and len(side_a.split('.')[1]) == 3: return val_a
        if '.' in side_b and len(side_b.split('.')[1]) == 3: return val_b
        
        return val_b if isinstance(val_b, int) else val_a

    # 2. Single-sided multiplier (e.g., "2 *")
    # Only returns if the number is NOT in price format (x.xx)
    single_mult = re.search(r'\b(\d+(?:\.\d+)?)\s*[\*xX×]', line)
    if single_mult:
        val_str = single_mult.group(1)
        if not is_price_format(val_str):
            return cast_to_numeric(val_str)

    return None

def is_end_of_receipt(line: str) -> bool:
    """Checks if the line contains a keyword indicating the end of the receipt footprint."""
    end_words = ["אמצעי", "מע\"מ", "ישרכארט", "כאל", "כ.אשראי", "ויזה"]
    return any(word in line for word in end_words)

def parse_receipt_google(text: str) -> Dict[str, Any]:
    """
    Parses Google Vision output. Now includes logic to extract quantities from discount lines
    before skipping them, and strictly enforces multiplier-based quantity extraction.
    """
    chain = identify_chain(text)
    
    try:
        lines_data = json.loads(text)
    except Exception:
        lines_data = [{"text": line} for line in text.split("\n")]
        
    products = []
    current_barcode = None
    pending_barcode = None
    
    for row in lines_data:
        line_text = row.get("text", "")
        if not line_text.strip(): continue
        if is_end_of_receipt(line_text): break
        if is_ignored_line(line_text):
            payment_words = ["סה\"כ", "סה''כ", "תשלום", "אשראי", "TOTAL", "Total"]
            if any(w in line_text for w in payment_words):
                current_barcode = None
                pending_barcode = None
            continue
            
        line_clean = clean_ocr_artifacts(line_text)
        bcode = get_best_barcode(line_clean)
        has_price = bool(re.search(r'\d+\.\d{2}', line_clean))
        
        # Identify if this is a discount/promotion line
        is_discount = bool(re.search(r'-\d|\d-|\bהנחה\b|\bמוגבל\b|\bזיכוי\b|\bמבצע\b', line_clean))
        
        # NEW STRATEGY: Try to extract quantity even from discount lines
        qty_from_line = _extract_quantity_from_line(line_clean)

        if is_discount:
            # If we have an active product and found a quantity on the discount line, update it
            if current_barcode and qty_from_line is not None:
                if products[-1]["quantity"] == 1.0:
                    products[-1]["quantity"] = qty_from_line
            
            # Skip processing this line further as a new product unless it has a solid barcode
            if not bcode or (len(bcode) < 8 and not bcode.startswith('729')):
                continue
        
        # Standard product processing
        if bcode:
            qty = qty_from_line or 1.0
            if has_price:
                products.append({"barcode": bcode, "quantity": qty})
                current_barcode = bcode
                pending_barcode = None
            else:
                pending_barcode = bcode
        else:
            if has_price:
                if pending_barcode:
                    qty = qty_from_line or 1.0
                    products.append({"barcode": pending_barcode, "quantity": qty})
                    current_barcode = pending_barcode
                    pending_barcode = None
                elif current_barcode and qty_from_line is not None:
                    if products[-1]["quantity"] == 1.0:
                        products[-1]["quantity"] = qty_from_line
                        current_barcode = None
            elif current_barcode and qty_from_line is not None:
                # Handle cases where quantity is on a standalone line (e.g., "2 *")
                if products[-1]["quantity"] == 1.0:
                    products[-1]["quantity"] = qty_from_line
                current_barcode = None
                
    return {"chain": chain, "products": products}

