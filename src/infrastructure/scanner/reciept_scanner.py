import pytesseract
from pytesseract import Output
import cv2
import re
import pandas as pd
import numpy as np
from bidi.algorithm import get_display

class FinalReceiptParserV8:
    def __init__(self):
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    def enhance_image(self, image_path):
        """עיבוד תמונה אופטימלי"""
        img = cv2.imread(image_path)
        if img is None: raise Exception("Image not found")
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # הגדלה פי 2.5 - הוכח כאיזון הכי טוב
        img_resized = cv2.resize(gray, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)
        
        # חידוד עדין
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(img_resized, -1, kernel)
        
        # טשטוש קל
        blurred = cv2.GaussianBlur(sharpened, (3, 3), 0)
        
        enhanced = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 31, 5
        )
        return enhanced

    def clean_ocr_text(self, text):
        text = text.replace('|', '1').replace('l', '1').replace('I', '1').replace(']', '1').replace('[', '1')
        text = text.replace('o', '0').replace('O', '0').replace('S', '5')
        return text

    def parse_receipt(self, image_path):
        print(f"Scanning V8 (Precision Grouping): {image_path}...")
        processed_img = self.enhance_image(image_path)
        
        d = pytesseract.image_to_data(processed_img, lang='heb+eng', config=r'--oem 3 --psm 6', output_type=Output.DICT)
        df = pd.DataFrame(d)
        df = df[df['text'].str.strip() != '']
        df['text'] = df['text'].astype(str)
        
        # --- תיקון קריטי: קיבוץ שורות עדין יותר ---
        # במקום 35, נשתמש ב-15. זה יפריד שורות שנדבקו אחת לשנייה.
        df['line_group'] = (df['top'] / 15).astype(int) 

        products = []
        header_lines = []
        table_started = False
        
        table_headers = ['ברקוד', 'פריט', 'שם', 'כמות', 'מחיר', 'סה"כ', 'קוד', 'יח']
        blacklist = ['2006', '2024', '2025', '300', '400', '500', '250', '1000', '52149', '7401964', '8455125', '6793978']

        for line_id, group in df.groupby('line_group'):
            # סינון שורות קצרות מדי (רעש)
            if len(group) < 2: continue

            row_words = group.sort_values('left')
            full_line_text = " ".join(row_words['text'])
            clean_line = self.clean_ocr_text(full_line_text)
            
            # --- Anchor ---
            if not table_started:
                if any(h in full_line_text for h in table_headers) or re.search(r'\b729\d{9,10}\b', clean_line):
                    table_started = True
                else:
                    header_lines.append(full_line_text)
                    continue

            # --- הסרת מספר שורה בסוף ---
            if len(row_words) > 2:
                last_word = self.clean_ocr_text(row_words.iloc[-1]['text'])
                # הסרת מספרים קטנים (1-100) בסוף השורה
                if last_word.isdigit() and int(last_word) < 100:
                    clean_line = clean_line.rsplit(' ', 1)[0]

            # זיהוי ברקוד
            numbers = re.findall(r'\b\d+\b', clean_line)
            barcode = None
            
            # א. ארוך
            longs = [n for n in numbers if len(n) >= 7 and n not in blacklist]
            if longs:
                best = max(longs, key=len)
                for b in longs:
                    if b.startswith('729'): best = b; break
                barcode = best
            
            # ב. קצר (בקצוות)
            elif not barcode:
                shorts = [n for n in numbers if 2 <= len(n) <= 5 and n not in blacklist]
                for sb in shorts:
                    if (clean_line.startswith(sb) or clean_line.endswith(sb)) and int(sb) > 20:
                        barcode = sb; break
            
            if barcode:
                # חילוץ כמות משופר
                decimals = [float(x) for x in re.findall(r'\b\d+\.\d+\b', clean_line)]
                integers = [float(x) for x in re.findall(r'\b\d+\b', clean_line) if x != barcode]
                
                quantity = 1.0
                unit_type = "יחידה"
                
                is_weight = 'קג' in full_line_text.replace('"', '') or 'Kg' in full_line_text
                
                if is_weight:
                    unit_type = "ק\"ג"
                    w_cands = [d for d in decimals if d < 10]
                    if w_cands: quantity = min(w_cands) # המשקל הוא הכי קטן
                else:
                    # למוצרי יחידה: אנחנו מחפשים 1.0, 2.0 וכו'
                    qty_cands = [d for d in decimals if d.is_integer() and d < 50]
                    qty_cands.extend([i for i in integers if i < 50])
                    
                    if qty_cands:
                        qty_cands.sort()
                        # --- תיקון לבעיית 34.0 ---
                        # אם הכמות שנבחרה (הקטנה ביותר) גדולה מ-10, זה כנראה מחיר ולא כמות.
                        # במקרה כזה, נחזור ל-1.0 כברירת מחדל.
                        best_candidate = qty_cands[0]
                        
                        if best_candidate == 1 or best_candidate == 1.0:
                            quantity = 1.0
                        elif best_candidate > 10: 
                            quantity = 1.0 # Fallback בטוח
                        else:
                            quantity = best_candidate # כנראה 2, 3 וכו'

                products.append({
                    "barcode": barcode,
                    "quantity": quantity,
                    "unit": unit_type,
                    "line": full_line_text
                })

        return {"header": header_lines, "products": products}

if __name__ == "__main__":
    parser = FinalReceiptParserV8()
    image_path = r'C:\Users\User\final_project\StockUp\src\infrastructure\scanner\1766055302690-f2d35fe9-a16c-4635-806f-5b93b00c1ab6_1.jpg'
    
    try:
        data = parser.parse_receipt(image_path)
        
        print("\n=== HEADER ===")
        for l in data['header']: print(get_display(l))

        print("\n" + "="*80)
        print(f"| {'Barcode':<15} | {'Qty':<5} | {'Unit':<6} | {'Original Line'}")
        print("="*80)
        
        for p in data['products']:
            orig = get_display(p['line'])
            print(f"| {p['barcode']:<15} | {p['quantity']:<5} | {p['unit']:<6} | {orig}...")
            
    except Exception as e:
        print(f"Error: {e}")