import os
import io
import json
from src.infrastructure.logger import app_logger
from src.infrastructure.scanner.extractors.image_extractor import client, vision, _reconstruct_vision_text

ENABLE_DEBUG = os.environ.get("ENABLE_DEBUG", "False").lower() == "true"

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from a PDF file using Google Vision API.
    Works for both native/digital PDFs and scanned PDFs.
    Returns the concatenated JSON text from all pages.
    """
    if not client or not vision:
        app_logger.warning("Google Vision client not available. Cannot process PDF.")
        return "[]"
        
    text_content = []
    try:
        with io.open(pdf_path, 'rb') as f:
            content = f.read()
            
        input_config = vision.InputConfig(content=content, mime_type='application/pdf')
        feature = vision.Feature(type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)
        request = vision.AnnotateFileRequest(input_config=input_config, features=[feature])
        
        response = client.batch_annotate_files(requests=[request])
        
        if response.responses and response.responses[0].responses:
            for page_response in response.responses[0].responses:
                if page_response.error.message:
                    app_logger.warning(f"Error on PDF page: {page_response.error.message}")
                    continue
                    
                page_json_str = _reconstruct_vision_text(page_response)
                try:
                    page_lines = json.loads(page_json_str)
                    text_content.extend(page_lines)
                except json.JSONDecodeError:
                    pass
                    
        # Optional Debug Logging
        if ENABLE_DEBUG:
            debug_dir = os.path.join(os.getcwd(), "results", "raw")
            os.makedirs(debug_dir, exist_ok=True)
            file_name = os.path.basename(pdf_path)
            name_without_ext = os.path.splitext(file_name)[0]
            debug_file_path = os.path.join(debug_dir, f"{name_without_ext}_pdf_vision_debug.txt")
            readable_text = "\n".join([line["text"] for line in text_content])
            with open(debug_file_path, "w", encoding="utf-8") as f:
                f.write(readable_text)
                
        return json.dumps(text_content, ensure_ascii=False)
        
    except Exception as e:
        app_logger.warning(f"Error extracting text from PDF {pdf_path}: {e}")
        return "[]"
