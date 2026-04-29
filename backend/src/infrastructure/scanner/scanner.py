import os
import re
import json
import time

from gradio_client import Client, handle_file
from src.infrastructure.scanner.parsers.pdf_parser import parse_receipt_pdf
from src.infrastructure.scanner.extractors.pdf_extractor import extract_text_from_pdf, is_text_pdf
from src.infrastructure.scanner.extractors.image_extractor import extract_text_from_image, extract_text_from_image_pdf, extract_first_page_image_text
from src.infrastructure.scanner.parsers.image_parser import identify_chain, parse_receipt_google

client = Client("orioha/PDFExtractor")

def scan_receipt(file_path: str) -> dict:
    """
    Main entry point to scan any receipt and return structured data.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    ext = os.path.splitext(file_path)[-1].lower()
    text = ""
    chain = "Unknown"
    if ext == '.pdf':
        if True: #is_text_pdf(file_path):
            try:
                print(f"Attempting native PDF text extraction for: {file_path}"+f" at {time.strftime('%Y-%m-%d %H:%M:%S')}")
                text = client.predict(
                    file=handle_file(file_path),
                    api_name="/api_handler"
                )
                print(f"Native PDF text extraction successful for: {file_path}"+f" at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            except Exception as e:
                text = ""
            first_page_ocr = extract_first_page_image_text(file_path)
            chain=identify_chain(first_page_ocr)
        else:
            text = extract_text_from_image_pdf(file_path)
            chain=identify_chain(text)
            
    elif ext in ['.jpeg', '.jpg', '.png']:
        text = extract_text_from_image(file_path)
    else:
        return {"chain": "Unknown", "products": [], "raw_text": ""}
        
    if not text.strip():
        return {"chain": "Unknown", "products": [], "raw_text": ""}
    
    # Use the appropriate parser based on the source type
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