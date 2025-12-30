import pytesseract
from pytesseract import Output
import cv2
import re
import pandas as pd
import numpy as np
from bidi.algorithm import get_display
from pdf2image import convert_from_path
import os
import pdfplumber

class ReceiptParser:
    def __init__(self):
        pytesseract.pytesseract.tesseract_cmd = r'tools\Tesseract-OCR\tesseract.exe'
        self.poppler_path = r'tools\poppler-25.12.0\Library\bin' 

    def load_file(self, file_path):
        """
        טוען קובץ. בודק אם הוא PDF דיגיטלי.
        מחזיר: (data_list, is_digital)
        """
        if not os.path.exists(file_path): raise Exception(f"File not found: {file_path}")
        
        # --- ניסיון 1: קריאה דיגיטלית (מהירה ומדויקת) ---
        if file_path.lower().endswith('.pdf'):
            try:
                with pdfplumber.open(file_path) as pdf:
                    # בדיקה מקדימה: האם יש טקסט בעמוד הראשון?
                    if len(pdf.pages) > 0 and len(pdf.pages[0].extract_words()) > 5:
                        print("Detected Digital PDF. Extracting text directly...")
                        all_pages_dfs = []
                        
                        for page in pdf.pages:
                            words = page.extract_words()
                            if not words: continue
                            
                            # המרה למבנה DataFrame זהה לזה ש-Tesseract מייצר
                            df = pd.DataFrame(words)
                            # pdfplumber נותן: x0, top, x1, bottom, text
                            # tesseract צריך: left, top, width, height, text
                            df = df.rename(columns={'x0': 'left', 'text': 'text'})
                            
                            # המרה ל-int וחישוב רוחב/גובה
                            df['left'] = df['left'].astype(int)
                            df['top'] = df['top'].astype(int)
                            df['width'] = (df['x1'] - df['left']).astype(int)
                            df['height'] = (df['bottom'] - df['top']).astype(int)
                            
                            # סינון עמודות רלוונטיות בלבד
                            all_pages_dfs.append(df[['left', 'top', 'width', 'height', 'text']])
                            
                        return all_pages_dfs, True # True מסמן שזה דיגיטלי
            except Exception as e:
                print(f"Digital parsing failed (falling back to OCR): {e}")

        # --- ניסיון 2: המרה לתמונות ו-OCR (לסריקות) ---
        if file_path.lower().endswith('.pdf'):
            print("Converting PDF to High-Res Images (300 DPI)...")
            try:
                abs_path = os.path.abspath(file_path)
                pil_images = convert_from_path(abs_path, dpi=300, poppler_path=self.poppler_path)
                images = [cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR) for img in pil_images]
                return images, False # False מסמן שצריך OCR
            except Exception as e: raise Exception(f"PDF Error: {e}")
        else:
            try:
                img = cv2.imdecode(np.fromfile(file_path, np.uint8), cv2.IMREAD_COLOR)
                if img is None: raise Exception("Empty image")
                return [img], False
            except Exception as e: raise Exception(f"Image Error: {e}")

    def enhance_image(self, img):
        if img is None: return None
        height, width = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        scale = 2.5 if width < 1000 else 1.0 
        img_resized = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        blurred = cv2.GaussianBlur(img_resized, (3, 3), 0)
        return cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 5)

    def clean_ocr_text(self, text):
        text = text.replace('|', '1').replace('l', '1').replace('I', '1').replace(']', '1').replace('[', '1').replace('n', 'ח')
        text = text.replace('o', '0').replace('O', '0').replace('S', '5').replace(',', '.').replace('״', '"').replace('״', '"')
        return text

    def parse_receipt(self, file_path):
        print(f"Processing: {file_path}...")
        
        # טעינה חכמה: מקבלים גם את הנתונים וגם האם זה דיגיטלי
        loaded_data, is_digital = self.load_file(file_path)
        
        all_results = {"chain name": "", "header": [], "products": []}
        self.table_started_global = False 
        
        for i, item in enumerate(loaded_data):
            print(f"Analyzing Page {i+1}...")
            # מעבירים את הפריט (תמונה או DataFrame) ואת הדגל
            page_data = self._process_single_page(item, is_digital)
            
            all_results["header"].extend(page_data["header"])
            all_results["products"].extend(page_data["products"])
            all_results["chain name"] = page_data["chain name"] or all_results["chain name"]
        
        # --- לוגיקה חדשה: אם לא מצאנו שם רשת בטקסט, סורקים את הלוגו ---
        if (not all_results["chain name"] or all_results["chain name"] == "רשת לא מזוהה") and is_digital and file_path.lower().endswith('.pdf'):
            print("Chain name not found in text layer. Scanning header image (OCR)...")
            detected_chain = self._extract_chain_from_header_image(file_path)
            if detected_chain:
                print(f"Success! Found chain in header image: {detected_chain}")
                all_results["chain name"] = detected_chain
            
        return all_results
    
    def _extract_chain_from_header_image(self, file_path):
        """
        פונקציית גיבוי: ממירה רק את החלק העליון של העמוד הראשון לתמונה
        ומבצעת עליו OCR כדי למצוא את הלוגו/שם הרשת.
        """
        try:
            # המרת העמוד הראשון בלבד
            images = convert_from_path(file_path, first_page=1, last_page=1, dpi=300, poppler_path=self.poppler_path)
            if not images: return None
            
            img = cv2.cvtColor(np.array(images[0]), cv2.COLOR_RGB2BGR)
            
            # חיתוך: לוקחים רק את ה-20% העליונים של התמונה (שם נמצא הלוגו)
            height, width = img.shape[:2]
            header_crop = img[0:int(height * 0.25), 0:width]
            
            # שיפור תמונה (Enhance)
            processed_header = self.enhance_image(header_crop)
            
            # ביצוע OCR
            text = pytesseract.image_to_string(processed_header, lang='heb+eng', config='--psm 6')
            
            # חיפוש ברשימת הרשתות
            # מנקים שורות חדשות כדי לאחד הכל לשורה אחת ארוכה לחיפוש
            clean_text = text.replace('\n', ' ').replace('\r', ' ')
            return self._chain_name_in_line(clean_text)
            
        except Exception as e:
            print(f"Header OCR failed: {e}")
            return None

    def _process_single_page(self, input_data, is_digital):
        # --- שלב 1: הכנת ה-DataFrame ---
        if is_digital:
            # אם זה דיגיטלי, קיבלנו כבר DataFrame מוכן
            df = input_data
        else:
            # אם זה סרוק, קיבלנו תמונה -> מבצעים עיבוד תמונה ו-OCR
            processed_img = self.enhance_image(input_data)
            if processed_img is None: return {"chain name": "", "header": [], "products": []}
            
            d = pytesseract.image_to_data(processed_img, lang='heb+eng', config=r'--oem 3 --psm 6', output_type=Output.DICT)
            df = pd.DataFrame(d)

        # --- שלב 2: לוגיקת הפרסור (זהה לשני המקרים) ---
        if df.empty: return {"chain name": "", "header": [], "products": []}
        
        # ניקוי שורות ריקות (רלוונטי בעיקר ל-OCR)
        if 'text' in df.columns:
            df = df[df['text'].str.strip() != '']
            df['text'] = df['text'].astype(str)
        
        # התאמת Grouping: בדיגיטלי ה-Top הוא ב-Points ולכן קטן יותר (יחס של בערך 1:3)
        # בסרוק (DPI 300) ה-Top הוא בפיקסלים ולכן גדול
        group_divider = 10 if is_digital else 30
        df['line_group'] = (df['top'] / group_divider).astype(int) 

        products = []
        header_lines = []
        
        header_keywords = ['שם פריט', 'ברקוד', 'כמות', 'מחיר', 'ש. פריט', 'מידה', 'תיאור', 'הנחה', 'ריחמ']
        global_skip_keywords = [
            'רשת חנויות', 'עוסק מורשה', 'טלפון', 'פקס', 'דואר אלקטרוני', 
            'חשבונית', 'העתק', 'לכבוד', 'בגין הזמנה', 'תאריך', 'שעה', 
            'סה"כ', 'מע"מ', 'מזומן', 'אשראי', 'חתימה', 'לקוח', 'עמוד', 'דף', 
            'סוכן', 'אספקה', 'חוסרים', 'ממחסן', 'ויזה', 'כאל', 'שיק', 'בנק', 'בבית'
        ]

        chain_name_found = False
        ch = ""


        for line_id, group in df.groupby('line_group'):
            row_words = group.sort_values('left')
            conf = row_words['conf'].astype(float).mean() if 'conf' in row_words.columns else 100.0
            reversed_row_list = row_words['text'].to_list()[::-1] if not is_digital else [str(w)[::-1] if not (re.match(r'\b(\d+\.\d{2,3})\b', str(w)) or str(w).isdigit()) else str(w) for w in row_words['text'].to_list()[::-1]]
            full_line_text = " ".join(reversed_row_list) 
            clean_line = self.clean_ocr_text(full_line_text)

            to_print = [f"[{i}] {w}" for i, w in enumerate(clean_line.split(" "))]
            # הדפסה לדיבוג - כדי לראות מה הוא קורא
            print(f"DEBUG Line: confident?:{conf} Words: {to_print}")

            if not chain_name_found:
                ch = self._chain_name_in_line(clean_line)
                if ch != "רשת לא מזוהה":
                    chain_name_found = True

            # --- תיקון: בדיקת תחילת טבלה *לפני* הסינון הגלובלי ---
            # זה מונע את המצב שבו המילה "מע"מ" בכותרת גורמת לדילוג על פתיחת הטבלה
            if not self.table_started_global:
                # 1. האם זו שורת הכותרת?
                if any(k in full_line_text for k in header_keywords):
                    self.table_started_global = True
                    header_lines.append(full_line_text)
                    print("Table started by Header Keywords") # לדיבוג
                    continue 

                # 2. האם זה ברקוד 729? (גיבוי למקרה שהכותרת לא זוהתה)
                if re.search(r'\b729\d{9,10}\b', clean_line):
                    self.table_started_global = True
                    print("Table started by 729 Barcode") # לדיבוג
                    # לא עושים continue כי השורה הזו היא כבר מוצר!
                else:
                    # אם הטבלה עוד לא התחילה וזו לא כותרת ולא מוצר 729 - זה זבל
                    header_lines.append(full_line_text)
                    continue
            
            # --- לוגיקת HEADER SKIP (עכשיו היא רצה רק בתוך הטבלה או בדפים הבאים) ---
            if any(k in full_line_text for k in global_skip_keywords):
                header_lines.append(full_line_text)
                continue
            
            # --- מכאן והלאה: קוד המוצרים (ללא שינוי מהגרסה העובדת שלך) ---
            if len(reversed_row_list) < 5:
                continue
                    
            barcode = reversed_row_list[1] 
            
            # הגנה: אם הברקוד לא ספרתי, דלג
            if not str(barcode).isdigit() or len(barcode) < 2: # המרה ל-str ליתר ביטחון
                print(f"Skipping line due to invalid barcode: {barcode}")
                continue

            quantity = 1.0
            unit_type = ""

            def found_kg(line):
                kgs = ["קג", 'ק"ג', "קילוגרם", "קילוגרמים", 'קילו', "גק", 'ג"ק', 'םרגוליק', 'םימרגוליק', "וליק"]
                for w in line:
                    for k in kgs:
                        if k in w: return True
                return False
            
            is_kg_found = found_kg(reversed_row_list)
            
            if not is_kg_found:
                unit_type = "יחידה"
                # try to find quantity in format X.000 or X.00 or X.0
                qty_matches = re.findall(r'\b(\d+\.0{1,3})\b', full_line_text)
                if qty_matches:
                    try: 
                        quantity = float(qty_matches[0])
                        if quantity == 0.0: quantity = 1.0
                    except: quantity = 1.0
            else:
                unit_type = "ק\"ג"
                qty_matches = re.findall(r'\b(\d+\.\d{2,3})\b', full_line_text)
                if qty_matches:
                    try: 
                        quantity = float(qty_matches[0])
                        if quantity == 0.0: quantity = 1.0
                    except: quantity = 1.0

            products.append({
                "barcode": barcode,
                "quantity": quantity,
                "unit": unit_type,
                "line": full_line_text
            })

        return {"chain name": ch, "header": header_lines, "products": products}
    
    def _chain_name_in_line(self, line: str) -> str:
        retail_chains = [
                        "קינג סטור", "מעיין אלפיים", "גוד פארם", "קרפור", "קוויק", 
                        "ביתן אונליין", "יינות ביתן", "מגה", "דור אלון", "אלונית", 
                        "וולט", "ויקטורי", "זול ובגדול", "ח. כהן", "טיב טעם", 
                        "מחסני השוק", "חצי חינם", "יוחננוף", "אושר עד", "נתיב החסד", 
                        "ברכל", "סאלח דבאח", "סופר ספיר", "סופר פארם", "סיטי מרקט", 
                        "סטופ מרקט", "עוף והודו ברקת", "פוליצר", "יילו", "סופר יודה", 
                        "פרשמרקט", "משנת יוסף", "קשת טעמים", "רמי לוי", "סופר קופיקס", 
                        "שופרסל", "Be", "שוק העיר", "שפע ברכת השם"
                    ]
        for chain in retail_chains:
            if chain in line:
                return chain
        return "רשת לא מזוהה"

if __name__ == "__main__":
    parser = ReceiptParser()
    file_path = r'C:\Users\User\final_project\StockUp\src\infrastructure\scanner\reciept_rami_levi_full_2.pdf'
    
    try:
        data = parser.parse_receipt(file_path)
        print(f"\nFound {len(data['products'])} products in chain: {data['chain name'][::-1] if data['chain name'] else 'Unknown'}\n")
        print("="*80)
        print(f"| {'Barcode':<15} | {'Qty':<5} | {'Unit':<6} | {'Original Line'}")
        print("="*80)
        for p in data['products']:
            orig = get_display(p['line'])
            print(f"| {p['barcode']:<15} | {p['quantity']:<5} | {p['unit']:<6} | {orig}")
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")