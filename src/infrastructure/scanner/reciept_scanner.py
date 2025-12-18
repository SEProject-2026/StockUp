import pytesseract
from pytesseract import Output
import cv2
import re
import pandas as pd
import numpy as np
from bidi.algorithm import get_display

class ReceiptParserV14:
    def __init__(self):
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    def enhance_image(self, image_path):
        img = cv2.imread(image_path)
        if img is None: raise Exception("Image not found")
        
        height, width = img.shape[:2]
        # חיתוך 45% מהשמאל
        crop_start_x = int(width * 0.45)
        cropped_img = img[:, crop_start_x:width]
        
        gray = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2GRAY)
        img_resized = cv2.resize(gray, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)
        
        blurred = cv2.GaussianBlur(img_resized, (3, 3), 0)
        enhanced = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 31, 5
        )
        return enhanced

    def clean_ocr_text(self, text):
        text = text.replace('|', '1').replace('l', '1').replace('I', '1').replace(']', '1').replace('[', '1')
        text = text.replace('o', '0').replace('O', '0').replace('S', '5')
        text = text.replace(',', '.') 
        return text

    def parse_receipt(self, image_path):
        print(f"Scanning V14 (Remove Line Numbers): {image_path}...")
        processed_img = self.enhance_image(image_path)
        
        d = pytesseract.image_to_data(processed_img, lang='heb+eng', config=r'--oem 3 --psm 6', output_type=Output.DICT)
        
        df = pd.DataFrame(d)
        df = df[df['text'].str.strip() != '']
        df['text'] = df['text'].astype(str)
        df['line_group'] = (df['top'] / 20).astype(int) 

        products = []
        header_lines = []
        table_started = False
        
        blacklist = ['2006', '2024', '2025', '300', '400', '500', '250', '1000', '52149', '7401964', '8455125', '010']
        
        for line_id, group in df.groupby('line_group'):
            row_words = group.sort_values('left') # מיון משמאל לימין (בתמונה)
            
            # --- שלב 1: הסרת מספר שורה ---
            # בקבלה עברית, מספר השורה הוא בצד ימין (הכי רחוק ב-X).
            # בגלל החיתוך שעשינו, הוא עכשיו המילה האחרונה או הראשונה בטקסט (תלוי איך Tesseract קורא).
            # בדרך כלל הוא המילה הראשונה ב-List הממוין (left הכי קטן = שמאל), אבל בעברית זה הפוך.
            # נבדוק את שני הקצוות.
            
            if len(row_words) > 1:
                # בדיקת המילה הכי ימנית (left הכי גדול)
                last_word = self.clean_ocr_text(row_words.iloc[-1]['text'])
                # בדיקת המילה הכי שמאלית (left הכי קטן)
                first_word = self.clean_ocr_text(row_words.iloc[0]['text'])

                # אם זה מספר קטן (1-30), נעיף אותו
                if first_word.isdigit() and int(first_word) <= 30:
                    row_words = row_words.iloc[1:]
                elif last_word.isdigit() and int(last_word) <= 30:
                    row_words = row_words.iloc[:-1]

            full_line_text = " ".join(row_words['text'])
            clean_line = self.clean_ocr_text(full_line_text)
            
            # Anchor Logic
            if not table_started:
                if re.search(r'729\d{8,12}', clean_line):
                    table_started = True
                else:
                    header_lines.append(full_line_text)
                    continue

            # --- זיהוי ברקוד ---
            numbers = re.findall(r'\b\d+\b', clean_line)
            barcode = None
            
            # ארוך
            longs = [n for n in numbers if len(n) >= 7 and n not in blacklist]
            if longs:
                best = max(longs, key=len)
                for b in longs:
                    if b.startswith('729'): best = b; break
                if len(best) == 14 and best.startswith('729'): best = best[:-1]
                barcode = best
            
            # קצר
            elif not barcode:
                shorts = [n for n in numbers if 2 <= len(n) <= 6 and n not in blacklist]
                for sb in shorts:
                    # תנאי מרוכך לירקות: 3 ספרות ומעלה
                    if (len(sb) >= 3 or clean_line.startswith(sb) or clean_line.endswith(sb)) and int(sb) > 30:
                        barcode = sb
                        break
            
            if barcode:
                # --- חילוץ כמות משופר ---
                
                # מוצאים הכל כולל שברים בלי נקודה (044)
                all_nums_str = re.findall(r'\b\d+\.?\d*\b', clean_line)
                candidates = []
                
                for s in all_nums_str:
                    try:
                        val = float(s)
                        if s == barcode or str(int(val)) == barcode: continue
                        
                        # סינון אחוזים (38% בשמנת)
                        if s in ['38', '5', '3']: # אחוזי שומן נפוצים
                             # בדיקה אם יש לידם '%' בטקסט המקורי - קשה לדעת כאן
                             # נסתמך על זה שאחוז הוא מספר שלם, וכמות היא לרוב 1.0
                             pass

                        if val < 50: candidates.append(val)
                    except: pass
                
                quantity = 1.0
                unit_type = "יחידה"

                if candidates:
                    candidates.sort() # מהקטן לגדול
                    
                    # --- תיקון: טיפול ב-044 (0.44) ---
                    # אם המספר מתחיל ב-0 אבל הוא לא שבר (למשל 044 שנקרא כ-44.0 או 0.0)
                    # נחפש מחרוזות שמתחילות ב-0
                    for s in all_nums_str:
                        if s.startswith('0') and len(s) > 1 and '.' not in s:
                             # מצאנו 044 -> נהפוך ל-0.44
                             try:
                                 new_val = float("0." + s[1:])
                                 candidates.insert(0, new_val) # דוחפים להתחלה כי זה קטן
                             except: pass

                    # סינון אפסים
                    candidates = [c for c in candidates if c > 0]
                    
                    if candidates:
                        best = candidates[0]
                        
                        # אם הכמות היא 38 (מהשמנת) ויש גם 2.0 -> ניקח 2.0
                        if best > 10 and len(candidates) > 1:
                            best = candidates[1]
                        
                        # תיקון 200 -> 2.00
                        if best >= 50: best = best / 100
                        
                        quantity = best
                        
                        if quantity < 1.0: unit_type = "ק\"ג"
                        elif quantity.is_integer(): unit_type = "יחידה"
                        else: unit_type = "ק\"ג"

                if quantity <= 0.01: quantity = 1.0
                if 'קג' in full_line_text.replace('"', ''): unit_type = "ק\"ג"

                products.append({
                    "barcode": barcode,
                    "quantity": quantity,
                    "unit": unit_type,
                    "line": full_line_text
                })

        return {"header": header_lines, "products": products}

if __name__ == "__main__":
    parser = ReceiptParserV14()
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
            print(f"| {p['barcode']:<15} | {p['quantity']:<5} | {p['unit']:<6} | {orig}")
            
    except Exception as e:
        print(f"Error: {e}")