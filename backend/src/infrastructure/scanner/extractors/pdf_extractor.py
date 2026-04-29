import os
import io
import json
import pdfplumber
import pypdfium2 as pdfium
from gradio_client import Client, handle_file
from src.infrastructure.logger import app_logger
from src.infrastructure.scanner.parsers.image_parser import identify_chain
from src.infrastructure.scanner.extractors.image_extractor import _reconstruct_vision_text

ENABLE_DEBUG = os.environ.get("ENABLE_DEBUG", "False").lower() == "true"

try:
    from google.cloud import vision
    from google.cloud import documentai_v1 as documentai
except ImportError:
    vision = None
    documentai = None
    app_logger.warning("Warning: google-cloud-vision or google-cloud-documentai not installed.")

from dotenv import load_dotenv
load_dotenv()

PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
PROCESSOR_ID = os.environ.get("DOCUMENT_AI_PROCESSOR_ID")
LOCATION = os.environ.get("GCP_LOCATION", "eu")

# Initialize Google Vision Client
try:
    if vision:
        api_key = os.environ.get("GOOGLE_VISION_API_KEY")
        if api_key:
            from google.api_core.client_options import ClientOptions
            client_options = ClientOptions(api_key=api_key)
            vision_client = vision.ImageAnnotatorClient(client_options=client_options)
        else:
            vision_client = vision.ImageAnnotatorClient()
    else:
        vision_client = None
except Exception as e:
    vision_client = None
    app_logger.warning(f"Warning: Could not initialize Google Vision API client. {e}")

# Initialize HuggingFace Client
hf_client = Client("orioha/PDFExtractor")

def _save_pdf_debug_text(pdf_path: str, content: str) -> None:
    if not ENABLE_DEBUG:
        return
    try:
        debug_dir = os.path.join(os.getcwd(), "results", "raw")
        if not os.path.exists(debug_dir):
            os.makedirs(debug_dir)
        file_name = os.path.basename(pdf_path)
        name_without_ext = os.path.splitext(file_name)[0]
        debug_file_path = os.path.join(debug_dir, f"{name_without_ext}_pdf_debug.txt")
        with open(debug_file_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        print(f"Warning: Failed to save PDF debug log. {e}")

def is_text_pdf(pdf_path: str) -> bool:
    """
    Checks if a PDF has native text by sampling the first page using pypdfium2 (extremely fast).
    """
    try:
        pdf = pdfium.PdfDocument(pdf_path)
        if len(pdf) == 0:
            return False
        page = pdf[0]
        textpage = page.get_textpage()
        text = textpage.get_text_bounded()
        if text and len([c for c in text if c.isalnum()]) > 10:
            return True
    except Exception:
        pass
    return False

def _extract_digital_pdf(file_path: str) -> str:
    """
    Extract text natively from a digital PDF file using HuggingFace space.
    """
    try:
        text = hf_client.predict(
            file=handle_file(file_path),
            api_name="/api_handler"
        )
        if text:
            _save_pdf_debug_text(file_path, text)
        return text
    except Exception as e:
        app_logger.warning(f"HF extraction failed: {e}")
        return ""

def _extract_scanned_pdf(file_path: str) -> str:
    """
    Extract text from an image-based PDF using Google Cloud Document AI.
    """
    if not documentai or not PROJECT_ID or not PROCESSOR_ID:
        app_logger.warning("Document AI not configured or installed.")
        return "[]"

    try:
        options = {"api_endpoint": f"{LOCATION}-documentai.googleapis.com"}
        doc_client = documentai.DocumentProcessorServiceClient(client_options=options)
        name = doc_client.processor_path(PROJECT_ID, LOCATION, PROCESSOR_ID)

        with open(file_path, "rb") as f:
            file_content = f.read()

        raw_document = documentai.RawDocument(content=file_content, mime_type='application/pdf')
        request = documentai.ProcessRequest(name=name, raw_document=raw_document)
        result = doc_client.process_document(request=request)
        
        document = result.document
        all_lines = []

        for page in document.pages:
            # Dictionary to group tokens by their vertical center position
            rows = {}
            # Threshold for grouping (how many inches/pixels apart to consider same line)
            threshold = 0.005 

            for token in page.tokens:
                # Get the vertical center of the token
                vertices = token.layout.bounding_poly.normalized_vertices
                if not vertices:
                    continue
                y_center = sum(v.y for v in vertices) / len(vertices)
                
                # Find if a row already exists within the threshold
                found_row = None
                for row_y in rows.keys():
                    if abs(row_y - y_center) < threshold:
                        found_row = row_y
                        break
                
                # Get token text
                start_index = token.layout.text_anchor.text_segments[0].start_index
                end_index = token.layout.text_anchor.text_segments[0].end_index
                text = document.text[int(start_index):int(end_index)].replace('\n', '').strip()

                if found_row is not None:
                    rows[found_row].append({'x': vertices[0].x, 'text': text})
                else:
                    rows[y_center] = [{'x': vertices[0].x, 'text': text}]

            # Sort rows by Y (top to bottom) and tokens within rows by X (left to right / right to left)
            for y in sorted(rows.keys()):
                # Sort tokens by X to maintain horizontal order
                sorted_tokens = sorted(rows[y], key=lambda i: i['x'])
                combined_line = " ".join(t['text'] for t in sorted_tokens)
                if combined_line.strip():
                    # Format exactly like the vision parser output expects: {"text": combined_line}
                    all_lines.append({"text": combined_line})

        return json.dumps(all_lines, ensure_ascii=False)

    except Exception as e:
        app_logger.warning(f"Document AI Extraction error: {e}")
        return "[]"


def _extract_first_page_vision(file_path: str) -> str:
    """
    Extracts ONLY the first page using Google Vision.
    Useful for digital PDFs where the chain logo/HP is embedded as an image.
    """
    if not vision_client:
        return "[]"
    
    try:
        with io.open(file_path, 'rb') as f:
            content = f.read()
            
        input_config = vision.InputConfig(content=content, mime_type="application/pdf")
        features = [vision.Feature(type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)]
        
        requests = [
            vision.AnnotateFileRequest(
                input_config=input_config,
                features=features,
                pages=[1]
            )
        ]
        
        response = vision_client.batch_annotate_files(requests=requests)
        
        for file_response in response.responses:
            for page_response in file_response.responses:
                if not page_response.error.message:
                    return _reconstruct_vision_text(page_response)
                    
    except Exception as e:
        app_logger.warning(f"Error extracting first page of PDF {file_path} with Vision: {e}")
        
    return "[]"


def process_pdf_receipt(file_path: str) -> tuple[str, str]:
    """
    Main handler for PDF receipts.
    Returns: (extracted_text, identified_chain)
    """
    if is_text_pdf(file_path):
        text = _extract_digital_pdf(file_path)
        chain = identify_chain(text)
        
        # Fallback: if the chain is unknown, the logo/HP might be an image at the top of the first page.
        if chain in ["Unknown", "Unknown Chain"]:
            first_page_ocr = _extract_first_page_vision(file_path)
            chain = identify_chain(first_page_ocr)
    else:
        text = _extract_scanned_pdf(file_path)
        chain = identify_chain(text)
        
    if not text.strip():
        return "", "Unknown"
        
    return text, chain
