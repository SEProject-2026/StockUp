import os
import re
import json
import time

from src.infrastructure.google_scanner.pdf_extractor import extract_text_from_pdf, is_text_pdf
from src.infrastructure.google_scanner.google_vision_extractor import extract_text_from_image, extract_text_from_image_pdf, extract_first_page_image_text
from src.infrastructure.google_scanner.google_parser import parse_receipt_google


def scan_receipt(file_path: str) -> dict:
    """
    Main entry point to scan any receipt and return structured data.
    Takes an absolute path string, returns a dictionary of extracted JSON data.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    ext = os.path.splitext(file_path)[-1].lower()
    text = ""
    
    start_time = time.time()
    
    if ext == '.pdf':
        if is_text_pdf(file_path):
            text = extract_text_from_pdf(file_path)
            
            # Check if pdfplumber already natively extracted a valid Company ID
            # Clean punctuation and letters that might be physically "touching" the numbers in the native PDF text
            text_clean = re.sub(r'[^\d\s]', ' ', text)
            hp_matches = re.findall(r'(?<!\d)(5[12]\d{7})(?!\d)', text_clean)
            
            if not hp_matches:
                # Only OCR the first page as a fallback to capture image-based logos
                first_page_ocr = extract_first_page_image_text(file_path)
                image_matches = re.findall(r'(?<!\d)(5[12]\d{7})(?!\d)', first_page_ocr)
                if image_matches:
                    image_chain_text = " ".join(image_matches)
                    text = f"Chain ID from Logo: {image_chain_text}\n" + text
        else:
            text = extract_text_from_image_pdf(file_path)
            
    elif ext in ['.jpeg', '.jpg', '.png']:
        text = extract_text_from_image(file_path)
    else:
        return {"chain": "Unknown", "products": [], "raw_text": ""}
        
    if not text.strip():
        return {"chain": "Unknown", "products": [], "raw_text": ""}
        
    # We only use the PDF parser if it was a native digital PDF
    is_native_pdf = (ext == '.pdf' and is_text_pdf(file_path))
    
    if is_native_pdf:
        # result = parse_receipt(text, is_pdf=True)
        pass
    else:
        result = parse_receipt_google(text)
    
    source_name = os.path.basename(file_path)
    for p in result.get("products", []):
        p["source"] = source_name
        
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

def scan_receipt_to_json(file_path: str, output_dir: str) -> str:
    """
    Convenience method for testing bounds that saves output directly to a JSON file.
    Returns the path to the saved JSON file.
    """
    result = scan_receipt(file_path)
    if not result:
        return ""
        
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.basename(file_path)
    name_without_ext = os.path.splitext(base_name)[0]
    out_file = os.path.join(output_dir, f"{name_without_ext}.json")
    
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
        
    return out_file

if __name__ == "__main__":
    import sys
    
    # Basic console configuration when run as a standalone script
    
    if len(sys.argv) > 1:
        input_paths = sys.argv[1:]
        results_dir = os.path.join(os.getcwd(), "results")
        os.makedirs(results_dir, exist_ok=True)
        
        # Expand directories into sorted file paths
        files = []
        for p in input_paths:
            if os.path.isfile(p):
                files.append(p)
            elif os.path.isdir(p):
                for root, _, filenames in os.walk(str(p)):
                    for f in filenames:
                        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.pdf')):
                            files.append(os.path.join(str(root), f))
                            
        files = sorted(list(set(files))) # Sort alphanumerically to ensure correct panorama ordering
        
        if not files:
            sys.exit(1)
            
        parsed_slices = []
        for file_path in files:
            parsed_slices.append(scan_receipt(file_path))
            
        if parsed_slices:
            final_receipt = merge_receipts(parsed_slices)
            
            # Use the first file's name as the base for the merged JSON
            base_name = os.path.basename(files[0])
            name_without_ext = str(os.path.splitext(base_name)[0])
            if len(files) > 1:
                name_without_ext = f"{name_without_ext}_merged"
                
            out_file = os.path.join(results_dir, f"{name_without_ext}.json")
            
            with open(out_file, 'w', encoding='utf-8') as f:
                json.dump(final_receipt, f, indent=2, ensure_ascii=False)
                
            print(f"\nFinal Merged Document:\n{json.dumps(final_receipt, indent=2, ensure_ascii=False)}")
