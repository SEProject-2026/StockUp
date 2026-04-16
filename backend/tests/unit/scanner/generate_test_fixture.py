import os
import sys
from pathlib import Path

# Ensure backend root is in python path
backend_path = str(Path(__file__).resolve().parent.parent.parent.parent)
sys.path.append(backend_path)

# Enable debug mode so test_recorder triggers
os.environ["ENABLE_DEBUG"] = "True"

from src.infrastructure.scanner.receipt_scanner import ReceiptScanner

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_test_fixture.py <path_to_image1> [<path_to_image2> ...]")
        return
        
    image_paths = sys.argv[1:]
    
    # Verify paths
    valid_paths = []
    for path in image_paths:
        # resolve absolute path for correctness
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path):
            valid_paths.append(abs_path)
        else:
            print(f"Error: File not found: {path}")
            
    if not valid_paths:
        print("No valid image paths provided.")
        return
        
    print(f"Processing {len(valid_paths)} image(s)...")
    scanner = ReceiptScanner()
    chain, data = scanner.parse_receipt(valid_paths)
    
    print("\n--- Process Complete ---")
    print(f"Detected chain: {chain}")
    print("The test files (raw text, JSON, and copied images) were successfully generated in 'tests/unit/scanner/results'.")

if __name__ == "__main__":
    main()
