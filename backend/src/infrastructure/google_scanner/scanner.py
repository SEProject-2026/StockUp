import os
import re
import json
import logging
import time

from src.infrastructure.google_scanner.pdf_extractor import extract_text_from_pdf, is_text_pdf
from src.infrastructure.google_scanner.google_vision_extractor import extract_text_from_image, extract_text_from_image_pdf, extract_first_page_image_text
from src.infrastructure.google_scanner.google_parser import parse_receipt_google

# Configure logging for integration into larger apps
logger = logging.getLogger(__name__)

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
        logger.info(f"[{os.path.basename(file_path)}] Processing PDF...")
        if is_text_pdf(file_path):
            logger.info("Detected natively digital text PDF.")
            text = extract_text_from_pdf(file_path)
            
            # Check if pdfplumber already natively extracted a valid Company ID
            # Clean punctuation and letters that might be physically "touching" the numbers in the native PDF text
            text_clean = re.sub(r'[^\d\s]', ' ', text)
            hp_matches = re.findall(r'(?<!\d)(5[12]\d{7})(?!\d)', text_clean)
            
            if not hp_matches:
                # Only OCR the first page as a fallback to capture image-based logos
                logger.info("No native Company ID found. Running OCR fallback on the first page...")
                first_page_ocr = extract_first_page_image_text(file_path)
                image_matches = re.findall(r'(?<!\d)(5[12]\d{7})(?!\d)', first_page_ocr)
                if image_matches:
                    image_chain_text = " ".join(image_matches)
                    text = f"Chain ID from Logo: {image_chain_text}\n" + text
            else:
                logger.info("Company ID found natively! Bypassing OCR fallback.")
        else:
            logger.info("Detected image-based PDF. Running OCR...")
            text = extract_text_from_image_pdf(file_path)
            
    elif ext in ['.jpeg', '.jpg', '.png']:
        logger.info(f"[{os.path.basename(file_path)}] Processing Image via OCR...")
        text = extract_text_from_image(file_path)
    else:
        logger.error(f"Unsupported file format: {ext}")
        return {"chain": "Unknown", "products": [], "raw_text": ""}
        
    if not text.strip():
        logger.warning(f"No text extracted from {file_path}")
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
        
    end_time = time.time()
    elapsed = end_time - start_time
    logger.info(f"[{source_name}] Scan completed in {elapsed:.2f} seconds.")
        
    return result

def merge_receipts(receipts: list) -> dict:
    """
    Takes a list of parsed receipt dictionaries (each containing 'chain' and 'products')
    and stitches them together to eliminate overlapping duplicate sequences (Count Once, Not Twice).
    """
    if not receipts:
        return {"chain": "Unknown", "products": []}
    
    # Extract the first valid chain name found across all slices
    final_chain = "Unknown"
    for r in receipts:
        if r.get("chain", "Unknown") != "Unknown":
            final_chain = r["chain"]
            break
            
    # Overlap Sequence Matcher (Panorama Stitching)
    merged_products = receipts[0].get("products", [])
    
    for next_receipt in receipts[1:]:
        next_products = next_receipt.get("products", [])
        if not next_products:
            continue
            
        max_overlap_idx = 0
        min_len = min(len(merged_products), len(next_products))
        
        # Test overlaps starting from the largest possible overlap sequence (min_len) down to 1
        for overlap_size in range(min_len, 0, -1):
            tail = [p['barcode'] for p in merged_products[-overlap_size:]]
            head = [p['barcode'] for p in next_products[:overlap_size]]
            if tail == head:
                max_overlap_idx = overlap_size
                break
                
        # Stitch by completely dropping the duplicated overlap sequence from the start of the next picture
        merged_products = merged_products + next_products[max_overlap_idx:]
        
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
        
    logger.info(f"Results successfully saved to: {out_file}")
    return out_file

if __name__ == "__main__":
    import sys
    
    # Basic console configuration when run as a standalone script
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
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
            logger.error("No valid image or pdf files found.")
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
                
            logger.info(f"Batched results successfully merged and saved to: {out_file}")
            print(f"\nFinal Merged Document:\n{json.dumps(final_receipt, indent=2, ensure_ascii=False)}")
    else:
        logger.error("Please provide at least one receipt file path or directory.")
