import os
import io
import json
import glob
import platform
import numpy as np
import cv2
from pdf2image import convert_from_path
from src.infrastructure.logger import app_logger


ENABLE_DEBUG = os.environ.get("ENABLE_DEBUG", "False").lower() == "true"
try:
    from google.cloud import vision
except ImportError:
    vision = None
    app_logger.warning("Warning: google-cloud-vision not installed.")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    if vision:
        api_key = os.environ.get("GOOGLE_VISION_API_KEY")
        if api_key:
            from google.api_core.client_options import ClientOptions
            client_options = ClientOptions(api_key=api_key)
            client = vision.ImageAnnotatorClient(client_options=client_options)
        else:
            client = vision.ImageAnnotatorClient()
    else:
        client = None
except Exception as e:
    client = None
    app_logger.warning(f"Warning: Could not initialize Google Vision API client. {e}")


def _get_poppler_path():
    """
    Dynamically finds Poppler path based on the Operating System.
    """
    current_os = platform.system()
    
    if current_os == "Windows":
        user_appdata = os.environ.get('LOCALAPPDATA')
        if user_appdata:
            search_pattern = os.path.join(
                user_appdata, 'Microsoft', 'WinGet', 'Packages', 
                'oschwartz10612.Poppler*', 'poppler-*', 'Library', 'bin'
            )
            results = glob.glob(search_pattern)
            if results:
                return results[0]
                
    elif current_os == "Darwin":  # macOS
        brew_path = "/opt/homebrew/bin"
        if os.path.exists(os.path.join(brew_path, "pdftoppm")):
            return brew_path
            
    # For Linux (Render/Docker), returns None to use global PATH
    return None


def _preprocess_image(image_bytes: bytes) -> bytes:
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return image_bytes
            
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        bg_dilate = cv2.dilate(gray, np.ones((7,7), np.uint8))
        bg = cv2.medianBlur(bg_dilate, 21)
        diff = 255 - cv2.absdiff(gray, bg)
        denoised = cv2.normalize(diff, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)

        is_success, buffer = cv2.imencode(".jpg", denoised)
        if is_success:
            return buffer.tobytes()
    except Exception as e:
        app_logger.warning(f"Image preprocessing failed: {e}")
    return image_bytes


def _reconstruct_vision_text(response):
    if not response or not response.full_text_annotation or not response.full_text_annotation.pages:
        return "[]"
        
    items = []
    for page in response.full_text_annotation.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    word_text = "".join([symbol.text for symbol in word.symbols])
                    conf = sum([symbol.confidence for symbol in word.symbols]) / len(word.symbols) if word.symbols else 0.0
                    vertices = word.bounding_box.vertices
                    xs = [v.x for v in vertices if hasattr(v, 'x')]
                    ys = [v.y for v in vertices if hasattr(v, 'y')]
                    if not xs or not ys:
                        continue
                    items.append({
                        'text': word_text, 
                        'conf': conf, 
                        'x': sum(xs) / len(xs), 
                        'y': sum(ys) / len(ys), 
                        'box': [[v.x, v.y] for v in vertices]
                    })
                    
    if not items:
        return "[]"

    items.sort(key=lambda item: item['y'])
    lines = []
    current_line = []
    current_y = None
    
    heights = []
    for item in items:
        if len(item['box']) >= 4:
            heights.append(((item['box'][3][1] - item['box'][0][1]) + (item['box'][2][1] - item['box'][1][1])) / 2)
            
    median_height = sorted(heights)[len(heights)//2] if heights else 20
    y_threshold = max(median_height * 0.6, 12)
    
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


def _save_debug_text(image_path: str, text_json: str, pdf_page_index: int = 0) -> None:
    if not ENABLE_DEBUG:
        return
    try:
        debug_dir = os.path.join(os.getcwd(),"results", "raw")
        if not os.path.exists(debug_dir):
            os.makedirs(debug_dir)

        file_name = os.path.basename(image_path)
        name_without_ext = os.path.splitext(file_name)[0]
        debug_file_path = os.path.join(debug_dir, f"{name_without_ext}_ocr_debug_{pdf_page_index}.txt")
        
        data = json.loads(text_json)
        readable_text = "\n".join([line["text"] for line in data])
        
        with open(debug_file_path, "w", encoding="utf-8") as f:
            f.write(readable_text)
    except Exception as e:
        app_logger.warning(f"Warning: Failed to save debug text. {e}")


def extract_text_from_image(image_path: str) -> str:
    if not client:
        return "[]"
    try:
        with io.open(image_path, 'rb') as image_file:
            content = image_file.read()
        processed_content = _preprocess_image(content)
        image = vision.Image(content=processed_content)
        response = client.document_text_detection(image=image)
        if response.error.message:
            raise Exception(f"{response.error.message}")
        reconstructed_json = _reconstruct_vision_text(response)
        _save_debug_text(image_path, reconstructed_json)
        return reconstructed_json
    except Exception as e:
        app_logger.warning(f"Google Vision Error on {image_path}: {e}")
        return "[]"


def extract_text_from_image_pdf(pdf_path: str) -> str:
    if not client:
        return "[]"
    text_content = []
    try:
        poppler_path = _get_poppler_path()
        images = convert_from_path(pdf_path, poppler_path=poppler_path)
        for idx, img in enumerate(images):
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG')
            content = img_byte_arr.getvalue()
            processed_content = _preprocess_image(content)
            image = vision.Image(content=processed_content)
            response = client.document_text_detection(image=image)
            
            if response.error.message:
                continue
                
            page_data = json.loads(_reconstruct_vision_text(response))
            text_content.extend(page_data)
            _save_debug_text(pdf_path, json.dumps(page_data, ensure_ascii=False), pdf_page_index=idx)
            
    except Exception as e:
        app_logger.warning(f"Error processing image PDF {pdf_path}: {e}")
    return json.dumps(text_content, ensure_ascii=False)


def extract_first_page_image_text(pdf_path: str) -> str:
    if not client:
        return "[]"
    try:
        poppler_path = _get_poppler_path()
        images = convert_from_path(pdf_path, poppler_path=poppler_path, first_page=1, last_page=1)
        if images:
            open_cv_image = np.array(images[0])
            open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2BGR)
            height = open_cv_image.shape[0]
            cropped_image = open_cv_image[0:int(height * 0.25), :]
            
            is_success, buffer = cv2.imencode(".jpg", cropped_image)
            if not is_success:
                return "[]"
                
            content = buffer.tobytes()
            processed_content = _preprocess_image(content)
            image = vision.Image(content=processed_content)
            response = client.document_text_detection(image=image)
            
            if response.error.message:
                return "[]"
                
            return _reconstruct_vision_text(response)
    except Exception as e:
        app_logger.warning(f"Error processing first page of PDF {pdf_path}: {e}")
    return "[]"