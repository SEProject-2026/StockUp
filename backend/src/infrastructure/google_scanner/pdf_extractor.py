import pdfplumber

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text natively from a PDF file using pdfplumber.
    Returns the concatenated text from all pages.
    """
    text_content = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text)
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        
    return "\n".join(text_content)

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
