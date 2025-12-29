import pytesseract
from pytesseract import Output
import cv2
import re
import pandas as pd
import numpy as np
from bidi.algorithm import get_display
from pdf2image import convert_from_path
import os

class ReceiptParser:
    def __init__(self):
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        # עדכן לנתיב שלך
        self.poppler_path = r'C:\Program Files\poppler-25.12.0\poppler-25.12.0\Library\bin' 

    def load_file(self, file_path):
        if not os.path.exists(file_path): raise Exception(f"File not found: {file_path}")
        if file_path.lower().endswith('.pdf'):
            print("Converting PDF to High-Res Images (300 DPI)...")
            try:
                abs_path = os.path.abspath(file_path)
                pil_images = convert_from_path(abs_path, dpi=300, poppler_path=self.poppler_path)
                return [cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR) for img in pil_images]
            except Exception as e: raise Exception(f"PDF Error: {e}")
        else:
            try:
                img = cv2.imdecode(np.fromfile(file_path, np.uint8), cv2.IMREAD_COLOR)
                if img is None: raise Exception("Empty image")
                return [img]
            except Exception as e: raise Exception(f"Image Error: {e}")

    def enhance_image(self, img):
        if img is None: return None
        height, width = img.shape[:2]
        # crop_start_x = int(width) # חיתוך מחירים
        # cropped_img = img[:, crop_start_x:width]
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
        images = self.load_file(file_path)
        all_results = {"chain name": "", "header": [], "products": []}
        
        # משתנה גלובלי (בין דפים) שיזכור אם הטבלה כבר התחילה
        self.table_started_global = False 
        
        for i, img in enumerate(images):
            print(f"Analyzing Page {i+1}...")
            page_data = self._process_single_page(img)
            all_results["header"].extend(page_data["header"])
            all_results["products"].extend(page_data["products"])
            all_results["chain name"] = page_data["chain name"] or all_results["chain name"]
            
        return all_results

    def _process_single_page(self, original_img):
        processed_img = self.enhance_image(original_img)
        if processed_img is None: return {"chain name": "", "header": [], "products": []}

        d = pytesseract.image_to_data(processed_img, lang='heb+eng', config=r'--oem 3 --psm 4', output_type=Output.DICT)
        df = pd.DataFrame(d)
        if df.empty: return {"chain name": "", "header": [], "products": []}
        df = df[df['text'].str.strip() != '']
        df['text'] = df['text'].astype(str)
        df['line_group'] = (df['top'] / 25).astype(int) 

        products = []
        header_lines = []
        
        # מילות מפתח שמודיעות לנו: "הנה התחילה הטבלה"
        header_keywords = ['שם פריט', 'ברקוד', 'כמות', 'מחיר', 'ש. פריט', 'מידה', 'תיאור']
        
        # רשימה שחורה למספרים סוררים שבכל זאת עברו
        global_skip_keywords = [
            'רשת חנויות', 'עוסק מורשה', 'טלפון', 'פקס', 'דואר אלקטרוני', 
            'חשבונית', 'העתק', 'לכבוד', 'בגין הזמנה', 'תאריך', 'שעה', 
            'סה"כ', 'מע"מ', 'מזומן', 'אשראי', 'חתימה', 'לקוח', 'עמוד', 'דף', 
            'סוכן', 'אספקה', 'חוסרים', 'ממחסן', 'ויזה', 'כאל', 'שיק', 'בנק', 'בבית'
        ]

        chain_name_found = False

        for line_id, group in df.groupby('line_group'):
            row_words = group.sort_values('left')
            reversed_row_list = row_words['text'].to_list()[::-1]
            full_line_text = " ".join(reversed_row_list)
            clean_line = self.clean_ocr_text(full_line_text)
            to_print = " ".join([f"[{i}] {w}" for i, w in enumerate(reversed_row_list)])
            print(f"clean_line: {line_id}. {to_print}")

            if not chain_name_found:
                ch = self._chain_name_in_line(full_line_text)
                if ch != "רשת לא מזוהה":
                    chain_name_found = True

            # --- לוגיקת HEADER SKIP (התיקון החדש) ---
            if any(k in full_line_text for k in global_skip_keywords):
                header_lines.append(full_line_text)
                continue
            if not self.table_started_global:
                # 1. בדיקה אם זו שורת כותרת (מכילה מילים כמו "שם פריט")
                if any(k in full_line_text for k in header_keywords):
                    self.table_started_global = True
                    header_lines.append(full_line_text)
                    continue # מדלגים על שורת הכותרת עצמה

                # 2. בדיקה אם זה מוצר ראשון מובהק (ברקוד 729 ארוך)
                # זה תופס את המוצר הראשון גם אם ה-OCR פספס את הכותרת
                if re.search(r'\b729\d{9,10}\b', clean_line):
                    self.table_started_global = True
                    # לא עושים continue, כי השורה הזו היא כבר מוצר!
                else:
                    # זה עדיין זבל של Header (טלפונים, כתובות וכו')
                    header_lines.append(full_line_text)
                    continue
            
            # --- מכאן והלאה: קוד המוצרים הרגיל ---
            if len(reversed_row_list) < 5:
                continue
                    
            barcode: str = reversed_row_list[1] 
            if not barcode.isdigit():
                continue

            quantity = 1.0
            unit_type = ""

            def found_kg(line):
                for w in line:
                    kgs = ["קג", 'ק"ג', "קילוגרם", "קילוגרמים"]
                    for k in kgs:
                        if k in w:
                            return True
                return False
            
            is_kg_found = found_kg(reversed_row_list)
            if not is_kg_found:
                unit_type = "יחידה"
                # look for quantity like "1.00" or "2.00" or "1.000" or "2.000"
                qty_matches = re.findall(r'\b(\d+\.00{1,3})\b', full_line_text)
                if qty_matches:
                    try:
                        quantity = float(qty_matches[0])
                    except:
                        quantity = 1.0

            else:
                unit_type = "ק\"ג"
                # look for quantity like "0.44" or "1.20" or "2.506" or "0.500"
                qty_matches = re.findall(r'\b(\d+\.\d{2,3})\b', full_line_text)
                if qty_matches:
                    try:
                        quantity = float(qty_matches[0])
                    except:
                        quantity = 1.0
                        

            products.append({
                "barcode": barcode,
                "quantity": quantity,
                "unit": unit_type,
                "line": full_line_text
            })

        return {"chain name": ch,"header": header_lines, "products": products}
    
    def _chain_name_in_line(self, line: str) -> str:
        retail_chains = [
                        "קינג סטור",
                        "מעיין אלפיים",
                        "גוד פארם",
                        "קרפור",
                        "קוויק",
                        "ביתן אונליין",
                        "יינות ביתן",
                        "מגה",
                        "דור אלון",
                        "אלונית",
                        "וולט",
                        "ויקטורי",
                        "זול ובגדול",
                        "ח. כהן",
                        "טיב טעם",
                        "מחסני השוק",
                        "חצי חינם",
                        "יוחננוף",
                        "אושר עד",
                        "נתיב החסד",
                        "ברכל",
                        "סאלח דבאח",
                        "סופר ספיר",
                        "סופר פארם",
                        "סיטי מרקט",
                        "סטופ מרקט",
                        "עוף והודו ברקת",
                        "פוליצר",
                        "יילו",
                        "סופר יודה",
                        "פרשמרקט",
                        "משנת יוסף",
                        "קשת טעמים",
                        "רמי לוי",
                        "סופר קופיקס",
                        "שופרסל",
                        "Be",
                        "שוק העיר",
                        "שפע ברכת השם"
                    ]
        clean_line_for_search = line.replace('.', ' ').replace('-', ' ').replace('"', '').replace("'", "")
        
        for chain in retail_chains:
            clean_chain = chain.replace('"', '').replace("'", "")
            
            if clean_chain in clean_line_for_search:
                return chain
            chain_parts = clean_chain.split()
            if len(chain_parts) > 1:
                if all(part in clean_line_for_search for part in chain_parts):
                    return chain
                    
        return "רשת לא מזוהה"

if __name__ == "__main__":
    parser = ReceiptParser()
    file_path = r'C:\Users\User\final_project\StockUp\src\infrastructure\scanner\reciept_mahsanei_hashuk_full.pdf' 
    
    try:
        data = parser.parse_receipt(file_path)
        print(f"\nFound {len(data['products'])} products in chain: {data['chain name'][::-1]}\n")
        print("="*80)
        print(f"| {'Barcode':<15} | {'Qty':<5} | {'Unit':<6} | {'Original Line'}")
        print("="*80)
        for p in data['products']:
            orig = get_display(p['line'][:40])
            print(f"| {p['barcode']:<15} | {p['quantity']:<5} | {p['unit']:<6} | {orig}")
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")