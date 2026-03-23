import os
import pdfplumber

ENABLE_DEBUG = os.environ.get("ENABLE_DEBUG", "False").lower() == "true"

def _save_pdf_debug_text(pdf_path: str, content: str) -> None:
    """
    Saves the extracted PDF text to a 'debug' folder for verification.
    """
    if not ENABLE_DEBUG:
        return
    try:
        # Define and create debug directory in current execution path
        debug_dir = os.path.join(os.getcwd(), "results", "raw")
        if not os.path.exists(debug_dir):
            os.makedirs(debug_dir)
        
        # Create filename based on the original PDF name
        file_name = os.path.basename(pdf_path)
        name_without_ext = os.path.splitext(file_name)[0]
        debug_file_path = os.path.join(debug_dir, f"{name_without_ext}_pdf_debug.txt")
        
        with open(debug_file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        print(f"PDF debug text saved to: {debug_file_path}")
    except Exception as e:
        print(f"Warning: Failed to save PDF debug log. {e}")

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text natively from a PDF file using pdfplumber.
    Returns the concatenated text from all pages and saves a debug log.
    """
    text_content = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text)
                    
        full_text = "\n".join(text_content)
        
        # --- NEW: Save the extracted text for debugging ---
        if full_text:
            _save_pdf_debug_text(pdf_path, full_text)
        # --------------------------------------------------
        
        return full_text
        
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return ""

def is_text_pdf(pdf_path: str) -> bool:
    """
    Checks if a PDF has native text by sampling the first page.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                return False
            text = pdf.pages[0].extract_text()
            # If we found at least a few alphanumeric characters, it's a text PDF
            if text and len([c for c in text if c.isalnum()]) > 10:
                return True
    except Exception:
        pass
    return False
