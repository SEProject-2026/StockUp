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
import subprocess as sp

class ReceiptParser:
    def __init__(self):
        base_dir = os.getcwd()
        
        # בניית נתיבים אבסולוטיים (מלאים)
        tesseract_rel = r'tools\Tesseract-OCR\tesseract.exe'
        poppler_rel = r'tools\poppler-25.12.0\Library\bin'
        
        pytesseract.pytesseract.tesseract_cmd = os.path.join(base_dir, tesseract_rel)
        self.poppler_path = os.path.join(base_dir, poppler_rel)
        self.table_started_global = False
        self.table_ended_global = False

    def load_file(self, file_path):
        """
        טוען קובץ. בודק אם הוא PDF דיגיטלי.
        מחזיר: (data_list, is_digital)
        """
        if not os.path.exists(file_path): raise Exception(f"File not found: {file_path}")
        
        # --- ניסיון 1: קריאה דיגיטלית ---
        if file_path.lower().endswith('.pdf'):
            try:
                with pdfplumber.open(file_path) as pdf:
                    # בדיקה האם יש טקסט בעמוד הראשון
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

        # --- ניסיון 2: המרה לתמונות ו-OCR ---
        if file_path.lower().endswith('.pdf'):
            print("Converting PDF to High-Res Images (300 DPI)...")
            try:
                abs_path = os.path.abspath(file_path)
                images = convert_from_path(
                            abs_path,
                            dpi=300,
                            poppler_path=self.poppler_path
                        )
                images = [cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR) for img in images]
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

        # נתיבים לקבצים זמניים
        temp_in = os.path.abspath("page_temp_in.png")
        temp_out = os.path.abspath("page_temp_out.png")
        cv2.imwrite(temp_in, img)

        # 1. איתור נתיב הסקריפט (PowerShell)
        # מניח שהוא בתיקיית ה-src הנוכחית או בתיקיית tools
        script_dir = os.path.dirname(os.path.abspath(__file__))
        ps_script = os.path.join(script_dir, "textcleaner.ps1")
        if not os.path.exists(ps_script):
             # ניסיון שני: אולי זה בתיקיית השורש?
             ps_script = os.path.abspath("textcleaner.ps1")

        # 2. איתור נתיב ImageMagick (התיקייה בה נמצא magick.exe)
        # נשתמש במיקום היחסי לתיקיית הפרויקט
        project_root = os.getcwd()
        if 'src' in project_root: # אם הרצנו מתוך תיקייה פנימית
             project_root = os.path.abspath(os.path.join(project_root, '..', '..', '..'))
        
        im_dir = os.path.join(project_root, 'tools', 'ImageMagick-7.1.2-Q16')
        
        # אם התיקייה לא קיימת בדיוק בשם הזה, ננסה למצוא אותה דינמית
        if not os.path.exists(im_dir):
            tools_dir = os.path.join(project_root, 'tools')
            if os.path.exists(tools_dir):
                for d in os.listdir(tools_dir):
                    if "ImageMagick" in d:
                        im_dir = os.path.join(tools_dir, d)
                        break

        # 3. יצירת סביבת ריצה מותאמת (Environment Variables)
        # זה התיקון הקריטי! אנחנו אומרים ל-ImageMagick איפה הוא גר
        my_env = os.environ.copy()
        
        # הוספה ל-PATH כדי ש-PowerShell יזהה את הפקודה 'magick'
        my_env["PATH"] = im_dir + os.pathsep + my_env["PATH"]
        
        # משתנים קריטיים לגרסה ניידת כדי שתמצא את ה-Modules (כמו PNG decoder)
        my_env["MAGICK_HOME"] = im_dir
        my_env["MAGICK_CODER_MODULE_PATH"] = os.path.join(im_dir, "modules", "coders")
        my_env["MAGICK_CONFIGURE_PATH"] = im_dir

        # בדיקה שהסקריפט קיים
        if not os.path.exists(ps_script):
            print(f"[WARNING] textcleaner.ps1 not found via path: {ps_script}")
            return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # הפקודה המלאה
        cmd = [
            "powershell.exe",
            "-NoProfile", 
            "-ExecutionPolicy", "Bypass", 
            "-File", ps_script,
            "-InputFile", temp_in,
            "-OutputFile", temp_out,
            "-Grayscale",
            "-Enhance", "stretch",
            "-FilterSize", "25",
            "-Offset", "10",
            "-Sharpen", "1"
        ]

        try:
            # מריצים עם הפרמטר env=my_env
            sp.run(cmd, check=True, env=my_env, stdout=sp.DEVNULL, stderr=sp.DEVNULL)

            if os.path.exists(temp_out):
                cleaned_img = cv2.imread(temp_out)
                # ניקוי קבצים זמניים
                try:
                    os.remove(temp_in)
                    os.remove(temp_out)
                except: pass
                
                if cleaned_img is None:
                    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    
                return cv2.cvtColor(cleaned_img, cv2.COLOR_BGR2GRAY)
            else:
                print("Error: Output file not created by script.")
                return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        except Exception as e:
            # הדפסת שגיאה מפורטת רק אם זה נכשל
            print(f"PowerShell TextCleaner failed: {e}")
            return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


    def clean_ocr_text(self, text):
        text = text.replace('|', '1').replace('l', '1').replace('I', '1').replace(']', '1').replace('[', '1').replace('n', 'ח').replace('\u200f', "").replace('\\', "")
        text = text.replace('o', '0').replace('O', '0').replace('S', '5').replace(',', '.').replace('״', '"').replace('״', '"').replace('/', '7').replace('D', 'ק').replace('_', '')
        text = text.replace('T', 'ק').replace('Z', '2').replace('z', '2').replace('B', '8').replace('G', '6').replace('a', 'ג').replace('y', 'ק').replace('p', 'ק')
        text = 'פלפל' if text == '7979' else text
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
            self.table_started_global = False  # איפוס לדף הבא
            all_results["header"].extend(page_data["header"])
            all_results["products"].extend(page_data["products"])
            all_results["chain name"] = page_data["chain name"] or all_results["chain name"]
        
        # --- אם לא מצאנו שם רשת בטקסט, סורקים את הלוגו ---
        if (not all_results["chain name"] or all_results["chain name"] == "רשת לא מזוהה") and is_digital and file_path.lower().endswith('.pdf'):
            print("Chain name not found in text layer. Scanning header image (OCR)...")
            detected_chain = self._extract_chain_from_header_image(file_path)
            if detected_chain:
                print(f"Success! Found chain in header image: {detected_chain}")
                all_results["chain name"] = detected_chain
        
        if os.path.exists("page_temp_in.png"):
            try: os.remove("page_temp_in.png")
            except: pass

        if os.path.exists("page_temp_out.png"):
            try: os.remove("page_temp_out.png")
            except: pass
            
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
            text = pytesseract.image_to_string(processed_header, lang='heb', config='--psm 6')
            
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
        stop_keywords = ['סה"כ לתשלום', 'סה"כ כולל מע"מ', 'כרטיס', 'ויזה', 'שיק', 'מאסטרקארד', 'אשראי', 'חוסרים', 'וויזה', 'כאל']

        chain_name_found = False
        ch = ""


        for _, group in df.groupby('line_group'):
            row_words = group.sort_values('left')
            reversed_row_list = []
            if not is_digital:
                for w in row_words['text'].to_list()[::-1]:
                    cleaned_word = self.clean_ocr_text(w)
                    if cleaned_word and cleaned_word != '':
                        reversed_row_list.append(cleaned_word)
            else:
                for w in row_words['text'].to_list()[::-1]:
                    cleaned_word = self.clean_ocr_text(str(w)[::-1]) if not (re.match(r'\b(\d+\.\d{2,3})\b', str(w)) or str(w).isdigit()) else str(w)
                    if cleaned_word and cleaned_word != '':
                        reversed_row_list.append(cleaned_word)

            full_line_text = " ".join(reversed_row_list)

            to_print = [f"[{i}] {w}" for i, w in enumerate(reversed_row_list)]
            # הדפסה לדיבוג - כדי לראות מה הוא קורא
            print(f"DEBUG Line: {to_print}")

            if not chain_name_found:
                ch = self._chain_name_in_line(full_line_text)
                if ch != "רשת לא מזוהה":
                    chain_name_found = True

            if self.table_ended_global:
                continue
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
                if re.search(r'\b729\d{9,10}\b', full_line_text):
                    self.table_started_global = True
                    # לא עושים continue כי השורה הזו היא כבר מוצר!
                else:
                    # אם הטבלה עוד לא התחילה וזו לא כותרת ולא מוצר 729 - זה זבל
                    header_lines.append(full_line_text)
                    continue

            if any(s in full_line_text for s in stop_keywords):
                print(f"Table ended by Stop Keywords: {full_line_text}") 
                self.table_ended_global = True # חשוב: מסמן שהטבלה נגמרה
                # אופציונלי: אם אתה רוצה להפסיק לעבד את העמוד הזה לגמרי:
                break
            
            # --- לוגיקת HEADER SKIP (עכשיו היא רצה רק בתוך הטבלה או בדפים הבאים) ---
            if any(k in full_line_text for k in global_skip_keywords):
                header_lines.append(full_line_text)
                continue
            
            # --- מכאן והלאה: קוד המוצרים (ללא שינוי מהגרסה העובדת שלך) ---
            if len(reversed_row_list) < 5:
                continue
                    
            barcode = None
            possible_barcodes = []

            for w in reversed_row_list:
                if w.isdigit():
                    possible_barcodes.append(w)
                else:
                    break

            if not possible_barcodes:
                continue

            if len(possible_barcodes) > 1:
                barcode = possible_barcodes[1]
            else:
                barcode = possible_barcodes[0]

            if not barcode or len(str(barcode)) < 2:
                # print(f"Skipping line due to invalid barcode: {barcode}")
                continue

            quantity = 1.0
            unit_type = ""

            def found_kg(line):
                kgs = ["קג", 'ק"ג', "קילוגרם", "קילוגרמים", 'קילו', "גק", 'ג"ק', 'םרגוליק', 'םימרגוליק', "וליק", 'ה"ג', 'הג', 'גה', 'ג"ה']
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