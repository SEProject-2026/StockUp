import os
import io
import json
import glob
import numpy as np
import cv2
from pdf2image import convert_from_path

try:
    from google.cloud import vision
except ImportError:
    vision = None
    print("Warning: google-cloud-vision not installed.")

# Try to load from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    
    pass

# Initialize global client if possible
try:
    if vision:
        api_key = os.environ.get("GOOGLE_VISION_API_KEY")
        if api_key:
            # Use API Key
            from google.api_core.client_options import ClientOptions
            client_options = ClientOptions(api_key=api_key)
            client = vision.ImageAnnotatorClient(client_options=client_options)
        else:
            # Assumes GOOGLE_APPLICATION_CREDENTIALS environment variable is set
            client = vision.ImageAnnotatorClient()
    else:
        client = None
except Exception as e:
    client = None
    print(f"Warning: Could not initialize Google Vision API client. Check GOOGLE_VISION_API_KEY or GOOGLE_APPLICATION_CREDENTIALS. {e}")


def _preprocess_image(image_bytes: bytes) -> bytes:
    """
    Pre-processes an image to remove faint text reflections from the back of the page.
    Applies grayscale, thresholding, and morphology to sharpen dark text and erase faint text.
    """
    try:
        # Convert bytes to numpy array then to cv2 image
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return image_bytes # Fallback if decode fails
            
        # 1. Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 2. Apply adaptive thresholding to bring out the dark text blocks
        # block size 21, C=15 helps wipe out light gray artifacts (the reflections)
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 15
        )
        
        # 3. Median blur to remove tiny noise/salt-and-pepper after thresholding
        denoised = cv2.medianBlur(thresh, 3)

        # Convert back to bytes
        is_success, buffer = cv2.imencode(".jpg", denoised)
        if is_success:
            return buffer.tobytes()
            
    except Exception as e:
        print(f"Warning: Image pre-processing failed, falling back to original. {e}")
        
    return image_bytes

def _reconstruct_vision_text(response):
    """
    Reconstructs text from Google Vision API response in the same format as PaddleOCR.
    PaddleOCR format: JSON string of list of lines:
    [
        {
            "text": "line text",
            "words": [
                {"text": "word", "conf": 0.99}
            ]
        }
    ]
    """
    if not response or not response.full_text_annotation or not response.full_text_annotation.pages:
        return "[]"
        
    items = []
    
    for page in response.full_text_annotation.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    word_text = "".join([symbol.text for symbol in word.symbols])
                    # Get average confidence of the word
                    conf = sum([symbol.confidence for symbol in word.symbols]) / len(word.symbols) if word.symbols else 0.0
                    
                    # Calculate center coordinates to sort and group lines
                    vertices = word.bounding_box.vertices
                    # Sometimes vertices might be missing some coordinates in rare cases
                    xs = [v.x for v in vertices if hasattr(v, 'x')]
                    ys = [v.y for v in vertices if hasattr(v, 'y')]
                    
                    if not xs or not ys:
                        continue
                        
                    x_center = sum(xs) / len(xs)
                    y_center = sum(ys) / len(ys)
                    
                    # Also need full box for height estimation
                    box = [[v.x, v.y] for v in vertices]
                    
                    items.append({
                        'text': word_text, 
                        'conf': conf, 
                        'x': x_center, 
                        'y': y_center, 
                        'box': box
                    })
                    
    items.sort(key=lambda item: item['y'])
    
    lines = []
    current_line = []
    current_y = None
    
    if not items:
        return "[]"
        
    # Calculate median height
    heights = []
    for item in items:
        box = item['box']
        if len(box) >= 4:
            h1 = box[3][1] - box[0][1]
            h2 = box[2][1] - box[1][1]
            heights.append((h1 + h2) / 2)
            
    if heights:
        median_height = sorted(heights)[len(heights)//2]
    else:
        median_height = 20 # Fallback
        
    y_threshold = max(median_height * 0.4, 10)
    
    for item in items:
        if current_y is None:
            current_line.append(item)
            current_y = item['y']
        else:
            if abs(item['y'] - current_y) < y_threshold:
                current_line.append(item)
            else:
                current_line.sort(key=lambda x: x['x'])
                lines.append({
                    "text": " ".join(i['text'] for i in current_line),
                    "words": [{"text": i['text'], "conf": i['conf']} for i in current_line]
                })
                current_line = [item]
                current_y = item['y']
                
    if current_line:
        current_line.sort(key=lambda x: x['x'])
        lines.append({
            "text": " ".join(i['text'] for i in current_line),
            "words": [{"text": i['text'], "conf": i['conf']} for i in current_line]
        })
        
    return json.dumps(lines, ensure_ascii=False)


def extract_text_from_image(image_path: str) -> str:
    """
    Extracts text from an image file using Google Cloud Vision.
    """
    if not client:
        print("Google Vision client not initialized. Cannot extract text.")
        return "[]"
        
    try:
        with io.open(image_path, 'rb') as image_file:
            content = image_file.read()
            
        # Process the image to remove reflections
        processed_content = _preprocess_image(content)
            
        image = vision.Image(content=processed_content)
        # Using document_text_detection for dense text like receipts
        response = client.document_text_detection(image=image)
        
        if response.error.message:
            raise Exception(f"{response.error.message}")
            
        return _reconstruct_vision_text(response)
    except Exception as e:
        print(f"Google Vision Error on {image_path}: {e}")
        return "[]"


def extract_text_from_image_pdf(pdf_path: str) -> str:
    """
    Converts an image-based PDF to images, then runs Google Vision on each page.
    """
    if not client:
        print("Google Vision client not initialized. Cannot extract text.")
        return "[]"
        
    text_content = []
    try:
        poppler_search = glob.glob(r'C:\Users\User\AppData\Local\Microsoft\WinGet\Packages\oschwartz10612.Poppler*\poppler-*\Library\bin')
        poppler_path = poppler_search[0] if poppler_search else None
        
        images = convert_from_path(pdf_path, poppler_path=poppler_path)
        for img in images:
            # Convert PIL image to bytes
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG')
            content = img_byte_arr.getvalue()
            
            # Process the image to remove reflections
            processed_content = _preprocess_image(content)
            
            image = vision.Image(content=processed_content)
            response = client.document_text_detection(image=image)
            
            if response.error.message:
                print(f"API Error: {response.error.message}")
                continue
                
            page_data = json.loads(_reconstruct_vision_text(response))
            text_content.extend(page_data)
            
    except Exception as e:
        print(f"Error processing image PDF {pdf_path}: {e}")
        
    return json.dumps(text_content, ensure_ascii=False)


def extract_first_page_image_text(pdf_path: str) -> str:
    """
    Converts only the first page of a PDF to an image and runs Google Vision.
    Crops to the top 25% like the PaddleOCR version to save cost/time.
    """
    if not client:
        print("Google Vision client not initialized. Cannot extract text.")
        return "[]"
        
    try:
        poppler_search = glob.glob(r'C:\Users\User\AppData\Local\Microsoft\WinGet\Packages\oschwartz10612.Poppler*\poppler-*\Library\bin')
        poppler_path = poppler_search[0] if poppler_search else None
        
        images = convert_from_path(pdf_path, poppler_path=poppler_path, first_page=1, last_page=1)
        if images:
            # Convert PIL Image to OpenCV format to crop it
            open_cv_image = np.array(images[0])
            open_cv_image = open_cv_image[:, :, ::-1].copy()
            
            # Crop top 25%
            height = open_cv_image.shape[0]
            cropped_image = open_cv_image[0:int(height * 0.25), :]
            
            # Convert back to bytes for Google Vision
            is_success, buffer = cv2.imencode(".jpg", cropped_image)
            if not is_success:
                raise Exception("Failed to encode cropped image.")
                
            content = buffer.tobytes()
            
            # Process the image to remove reflections
            processed_content = _preprocess_image(content)
            
            image = vision.Image(content=processed_content)
            response = client.document_text_detection(image=image)
            
            if response.error.message:
                raise Exception(f"{response.error.message}")
                
            return _reconstruct_vision_text(response)
            
    except Exception as e:
        print(f"Error processing first page of PDF {pdf_path}: {e}")
        
    return "[]"
