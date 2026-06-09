import os
import json

from src.infrastructure.scanner.parsers.pdf_parser import parse_receipt_pdf
from src.infrastructure.scanner.parsers.image_parser import parse_receipt_google
from src.infrastructure.scanner.extractors.pdf_extractor import process_pdf_receipt
from src.infrastructure.scanner.extractors.image_extractor import extract_text_from_image

def scan_receipt(file_path: str) -> dict:
    """
    Main entry point to scan any receipt and return structured data.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    ext = os.path.splitext(file_path)[-1].lower()
    text = ""
    chain = "Unknown"
    
    # 1. Routing by extension to the correct Extractor
    if ext == '.pdf':
        text, chain = process_pdf_receipt(file_path)
    elif ext in ['.jpeg', '.jpg', '.png']:
        text = extract_text_from_image(file_path)
        # For pure images, the parser will identify the chain based on the text
    else:
        return {"chain": "Unknown", "products": [], "raw_text": ""}
        
    if not text.strip():
        return {"chain": "Unknown", "products": [], "raw_text": ""}
    
    # 2. Routing to the correct Parser based on source type
    if ext == '.pdf':
        result = parse_receipt_pdf(text, chain)
    else:
        result = parse_receipt_google(text)
        
    result["raw_text"] = text
    return result

def merge_receipts(receipts: list) -> dict:
    """
    Takes a list of parsed receipt dictionaries (each containing 'chain' and 'products')
    and stitches them together to eliminate overlapping duplicate sequences (Count Once, Not Twice).
    """
    if not receipts:
        return {"chain": "Unknown", "products": []}
    # Extract the first valid chain name found across all slices
    final_chain = "Unknown Chain"
    for r in receipts:
        if r.get("chain", "Unknown Chain") != "Unknown Chain":
            final_chain = r["chain"]
            break
            
    
    merged_products = receipts[0].get("products", [])
    
    for next_receipt in receipts[1:]:
        next_products = next_receipt.get("products", [])
        if not next_products:
            continue
        merged_products.extend(next_products)
        
    return {"chain": final_chain, "products": merged_products}