# src/infrastructure/scanner/receipt_scanner.py

import os
import re
import platform
import shutil
import subprocess as sp
from typing import Tuple, Dict, Any

import cv2
import numpy as np
import pandas as pd
import pdfplumber
import pytesseract
from pytesseract import Output
from pdf2image import convert_from_path
from src.domain.smart_home.enums import OCRMode

class ReceiptScanner:
    def __init__(self):
        """
        Cross-platform init:
        - Windows: uses tools/Tesseract-OCR/tesseract.exe + tools/poppler... if exists
        - macOS/Linux: uses `tesseract` from PATH and poppler from PATH (or /opt/homebrew/bin)
        """
        system = platform.system()
        base_dir = os.getcwd()

        # -------- Tesseract --------
        if system == "Windows":
            tesseract_rel = os.path.join("tools", "Tesseract-OCR", "tesseract.exe")
            tesseract_path = os.path.join(base_dir, tesseract_rel)

            if os.path.exists(tesseract_path):
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
            else:
                # fallback to PATH
                found = shutil.which("tesseract")
                if found:
                    pytesseract.pytesseract.tesseract_cmd = found
                else:
                    # לא מפילים כאן — לפעמים משתמשים רק ב-digital PDF ללא OCR
                    print("[WARN] Tesseract not found on Windows. OCR may fail.")

            poppler_rel = os.path.join("tools", "poppler-25.12.0", "Library", "bin")
            poppler_path = os.path.join(base_dir, poppler_rel)
            self.poppler_path = poppler_path if os.path.exists(poppler_path) else None
            if self.poppler_path is None:
                print("[WARN] Poppler tools folder not found. PDF->images may fail unless poppler is installed in PATH.")

        else:
            # macOS / Linux
            found = shutil.which("tesseract")
            if not found:
                # common brew paths
                if os.path.exists("/opt/homebrew/bin/tesseract"):
                    found = "/opt/homebrew/bin/tesseract"
                elif os.path.exists("/usr/local/bin/tesseract"):
                    found = "/usr/local/bin/tesseract"

            if found:
                pytesseract.pytesseract.tesseract_cmd = found
            else:
                # שוב: לא מפילים כאן — כי digital PDF יכול לעבוד בלי tesseract
                print("[WARN] Tesseract not found. Install: brew install tesseract tesseract-lang")

            # poppler - pdf2image expects pdfinfo/pdftoppm available
            # אפשר גם להצביע על /opt/homebrew/bin כדי לעזור
            if os.path.exists("/opt/homebrew/bin"):
                self.poppler_path = "/opt/homebrew/bin"
            elif os.path.exists("/usr/local/bin"):
                self.poppler_path = "/usr/local/bin"
            else:
                self.poppler_path = None

        self.table_started_global = False
        self.table_ended_global = False

    def load_file(self, file_path: str):
        """
        טוען קובץ. בודק אם הוא PDF דיגיטלי.
        מחזיר: (data_list, is_digital)
        - digital: list[DataFrame]
        - scanned: list[np.ndarray images]
        """
        if not os.path.exists(file_path):
            raise Exception(f"File not found: {file_path}")

        # =====================================================
        # ניסיון 1: PDF דיגיטלי (ללא OCR)
        # =====================================================
        if file_path.lower().endswith(".pdf"):
            try:
                with pdfplumber.open(file_path) as pdf:
                    if len(pdf.pages) > 0:
                        first_words = pdf.pages[0].extract_words() or []
                        if len(first_words) > 5:
                            # print("Detected Digital PDF. Extracting text directly...")
                            all_pages_dfs = []

                            for page in pdf.pages:
                                words = page.extract_words() or []
                                if not words:
                                    continue

                                df = pd.DataFrame(words)

                                # pdfplumber -> תצורה דמוית Tesseract
                                # יש: x0, x1, top, bottom, text
                                df = df.rename(columns={"x0": "left", "text": "text"})

                                # לוודא עמודות קיימות לפני cast
                                for col in ["left", "top", "x1", "bottom"]:
                                    if col not in df.columns:
                                        raise Exception(f"Missing column '{col}' in pdfplumber output")

                                df["left"] = df["left"].astype(float).astype(int)
                                df["top"] = df["top"].astype(float).astype(int)
                                df["width"] = (df["x1"] - df["left"]).astype(float).astype(int)
                                df["height"] = (df["bottom"] - df["top"]).astype(float).astype(int)

                                all_pages_dfs.append(df[["left", "top", "width", "height", "text"]])

                            return all_pages_dfs, OCRMode.DIGITAL_PDF

            except Exception as e:
                print(f"Digital parsing failed (falling back to OCR): {e}")

        # =====================================================
        # ניסיון 2: PDF סרוק → תמונות → OCR
        # =====================================================
        if file_path.lower().endswith(".pdf"):
            print("Converting PDF to High-Res Images (300 DPI)...")
            try:
                abs_path = os.path.abspath(file_path)

                kwargs = {"dpi": 300}
                # poppler_path: רק אם קיים (עוזר גם ב-Mac אם נתת /opt/homebrew/bin)
                if self.poppler_path:
                    kwargs["poppler_path"] = self.poppler_path

                images = convert_from_path(abs_path, **kwargs)

                images = [cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR) for img in images]
                return images, OCRMode.SCANNED_PDF

            except Exception as e:
                raise Exception(f"PDF Error: {e}")

        # =====================================================
        # תיקון 3: קובץ תמונה רגיל (עם מניעת חיתוך)
        # =====================================================
        try:
            img = cv2.imread(file_path)
            if img is None:
                raise Exception("Empty image")

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # סף בינארי למציאת הטקסט
            thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

            # מציאת קואורדינטות הטקסט
            coords = np.column_stack(np.where(thresh > 0))
            
            # חישוב המלבן המינימלי
            rect = cv2.minAreaRect(coords)
            angle = rect[-1]
            
            # --- תיקון זווית חכם יותר לקבלות ---
            # קבלות הן בדרך כלל אנכיות. אם הזווית קיצונית (>45), ננרמל אותה
            if angle < -45:
                angle = 90 + angle
            elif angle > 45:
                angle = angle - 90
            
            # לפעמים התוצאה הפוכה בגלל גרסאות OpenCV שונות, אז נוודא שהזווית הגיונית
            # אנחנו רוצים לתקן רק יישור קל, לא לסובב את התמונה על הצד
            # רוב הקבלות עקומות בטווח של -10 עד 10 מעלות
            if abs(angle) > 45: 
                 angle = 0 # אם זה מסתבך, עדיף לא לגעת מאשר להרוס

            print(f"תיקון זווית: {angle:.2f}")

            # --- חישוב גבולות התמונה החדשים (כדי למנוע חיתוך) ---
            (h, w) = img.shape[:2]
            center = (w // 2, h // 2)

            # מטריצת הסיבוב
            M = cv2.getRotationMatrix2D(center, angle, 1.0)

            # חישוב ה-Sin וה-Cos של הזווית (בערך מוחלט)
            abs_cos = abs(M[0, 0])
            abs_sin = abs(M[0, 1])

            # חישוב הרוחב והגובה החדשים של התמונה המסובבת
            bound_w = int(h * abs_sin + w * abs_cos)
            bound_h = int(h * abs_cos + w * abs_sin)

            # עדכון המטריצה כדי שתזיז את התמונה למרכז החדש (במקום לחתוך אותה)
            M[0, 2] += bound_w / 2 - center[0]
            M[1, 2] += bound_h / 2 - center[1]

            # ביצוע הסיבוב עם הגבולות החדשים והרקע הלבן
            rotated = cv2.warpAffine(img, M, (bound_w, bound_h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))
            
            return [rotated], OCRMode.IMAGE

        except Exception as e:
            raise Exception(f"Image Error: {e}")

    def enhance_image(self, img):
        """
        Windows: מנסה PowerShell+ImageMagick אם קיים.
        macOS/Linux: OpenCV fallback בלבד (בלי powershell.exe).
        """
        if img is None:
            return None

        system = platform.system()

        # ---------- macOS/Linux: OpenCV-only ----------
        if system != "Windows":
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (3, 3), 0)
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            return gray

        # ---------- Windows: try PowerShell pipeline ----------
        temp_in = os.path.abspath("page_temp_in.png")
        temp_out = os.path.abspath("page_temp_out.png")
        cv2.imwrite(temp_in, img)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        ps_script = os.path.join(script_dir, "textcleaner.ps1")
        if not os.path.exists(ps_script):
            ps_script = os.path.abspath("textcleaner.ps1")

        project_root = os.getcwd()
        if "src" in project_root:
            project_root = os.path.abspath(os.path.join(project_root, "..", "..", ".."))

        im_dir = os.path.join(project_root, "tools", "ImageMagick-7.1.2-Q16")
        if not os.path.exists(im_dir):
            tools_dir = os.path.join(project_root, "tools")
            if os.path.exists(tools_dir):
                for d in os.listdir(tools_dir):
                    if "ImageMagick" in d:
                        im_dir = os.path.join(tools_dir, d)
                        break
        my_env = os.environ.copy()
        my_env["PATH"] = im_dir + os.pathsep + my_env["PATH"]
        my_env["MAGICK_HOME"] = im_dir
        my_env["MAGICK_CODER_MODULE_PATH"] = os.path.join(im_dir, "modules", "coders")
        my_env["MAGICK_CONFIGURE_PATH"] = im_dir

        if not os.path.exists(ps_script):
            print(f"[WARNING] textcleaner.ps1 not found via path: {ps_script}")
            return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        cmd = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", ps_script,
            "-InputFile", temp_in,
            "-OutputFile", temp_out,
            "-Grayscale",
            "-Enhance", "stretch",
            "-FilterSize", "15",
            "-Offset", "10",
            "-Sharpen", "1",
        ]
        
        try:
            sp.run(cmd, check=True, env=my_env, stdout=sp.DEVNULL, stderr=sp.DEVNULL)

            if os.path.exists(temp_out):
                cleaned_img = cv2.imread(temp_out)
                try:
                    os.remove(temp_in)
                    os.remove(temp_out)
                except:
                    pass

                if cleaned_img is None:
                    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

                return cv2.cvtColor(cleaned_img, cv2.COLOR_BGR2GRAY)

            print("Error: Output file not created by script.")
            return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        except Exception as e:
            print(f"PowerShell TextCleaner failed: {e}")
            return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    def clean_ocr_text(self, text: str) -> str:
        text = (
            text.replace("|", "1")
            .replace("l", "1")
            .replace("I", "1")
            .replace("]", "1")
            .replace("[", "1")
            .replace("n", "ח")
            .replace("\u200f", "")
            .replace("\\", "")
            .replace("i", "1")
        )
        text = (
            text.replace("o", "0")
            .replace("O", "0")
            .replace("S", "5")
            .replace(",", ".")
            .replace("״", '"')
            .replace("/", "7")
            .replace("D", "ק")
            .replace("_", "")
        )
        text = (
            text.replace("T", "ק")
            .replace("Z", "2")
            .replace("z", "2")
            .replace("B", "8")
            .replace("G", "6")
            .replace("a", "ג")
            .replace("y", "ק")
            .replace("p", "ק")
        )
        match = re.match(r'72\S0', text)
        if match:
            text = text.replace(text[2], '9')
        if text == "7979":
            text = "פלפל"
        elif text == "א":
            text = "x"
        
        return text

    def parse_receipt(self, file_path: str, *other_paths) -> Tuple[str, Dict]:
        # 1. איחוד כל הנתיבים לרשימה אחת
        all_paths = [file_path] + list(other_paths)
        
        # משתנים גלובליים לכל הקבצים יחד
        final_chain_name = ""
        # המילון שיחזיק את התוצאה הסופית המאוחדת
        # Key: Barcode, Value: (Quantity, Unit)
        aggregated_data = {} 

        loaded_data_list = []
        # 2. לולאה על כל הקבצים
        for current_path in all_paths:
            if not os.path.exists(current_path):
                print(f"[WARNING] File not found: {current_path}, skipping.")
                continue

            print(f"\n--- Processing File: {current_path} ---")

            try:
                loaded_data, is_digital = self.load_file(current_path)
                loaded_data_list += loaded_data
            except Exception as e:
                print(f"[ERROR] Failed to load {current_path}: {e}")
                continue

        # איפוס דגלים פר-קובץ (כדי שלא יושפעו מקובץ קודם)
        self.table_started_global = False
        self.table_ended_global = False
        
        current_file_chain = ""

        last_products = []  # לשמירת שלושת המוצרים האחרונים בעמוד הקודם

        # לולאה על העמודים בקובץ הנוכחי
        for i, item in enumerate(loaded_data_list):
            print(f"  Analyzing Page {i+1}...")
            
            # איפוס דגלים פר-עמוד (לפי הלוגיקה המקורית שלך)
            self.table_started_global = False if i == 0 or is_digital != OCRMode.IMAGE else self.table_started_global
            self.table_ended_global = False
            
            page_data = self._process_single_page(item, is_digital)
            
            # זיהוי שם הרשת (לוקחים את הראשון שמוצאים בקובץ)
            if not current_file_chain and page_data["chain name"]:
                current_file_chain = page_data["chain name"]

            # איחוד המוצרים למילון הסופי
            for prod in page_data["products"]:
                barcode = prod["barcode"]
                quantity = prod["quantity"]
                unit = prod["unit"]

                if barcode in last_products:
                    # print(f"    Skipping duplicate product (possible overlap): {barcode}")
                    continue

                aggregated_data[barcode] = (quantity, unit)

            # נשמור את השלושה מוצרים האחרונים כדי לבדוק חפיפה בין קבצים
            last_products = [prod["barcode"] for prod in page_data["products"][-6:]] if len(page_data["products"]) >= 6 else [prod["barcode"] for prod in page_data["products"]]

            
                        

            # --- Fallback: חיפוש שם רשת בתמונה (אם לא נמצא בטקסט) ---
            if (not current_file_chain or current_file_chain == "unidentified chain") \
               and is_digital == OCRMode.DIGITAL_PDF and current_path.lower().endswith(".pdf"):
                print("  Chain name not found in text. Scanning header image...")
                detected = self._extract_chain_from_header_image(current_path)
                if detected:
                    print(f"  Success! Found chain in header: {detected}")
                    current_file_chain = detected
            
            # עדכון שם הרשת הכללי (אם עדיין אין לנו, או אם הקודם היה לא מזוהה)
            if not final_chain_name or final_chain_name == "unidentified chain":
                final_chain_name = current_file_chain

            # ניקוי קבצים זמניים (אחרי כל קובץ)
            for fn in ["page_temp_in.png", "page_temp_out.png"]:
                if os.path.exists(fn):
                    try: os.remove(fn)
                    except: pass

        # print("\n--- Aggregation Complete ---")
        return final_chain_name, aggregated_data

    def _extract_chain_from_header_image(self, file_path):
        """
        גיבוי: ממירה רק את החלק העליון של העמוד הראשון לתמונה
        ומבצעת עליו OCR כדי למצוא את הלוגו/שם הרשת.
        """
        try:
            kwargs = {"first_page": 1, "last_page": 1, "dpi": 300}
            if self.poppler_path:
                kwargs["poppler_path"] = self.poppler_path

            images = convert_from_path(file_path, **kwargs)
            if not images:
                return None

            img = cv2.cvtColor(np.array(images[0]), cv2.COLOR_RGB2BGR)

            height, width = img.shape[:2]
            header_crop = img[0:int(height * 0.25), 0:width]

            processed_header = self.enhance_image(header_crop)

            try:
                text = pytesseract.image_to_string(processed_header, lang="heb", config="--psm 6")
            except Exception as e:
                # print(f"Header OCR failed (tesseract missing?): {e}")
                return None

            clean_text = text.replace("\n", " ").replace("\r", " ")
            return self._chain_name_in_line(clean_text)

        except Exception as e:
            # print(f"Header OCR failed: {e}")
            return None
    def _scan_english_numbers(self, img):
        d = pytesseract.image_to_data(
                img,
                lang="eng",
                config=r"--oem 3 --psm 6",
                output_type=Output.DICT,
            )
        df = pd.DataFrame(d)

        if df.empty:
            return {"chain name": "", "header": [], "products": []}

        if "text" in df.columns:
            df["text"] = df["text"].astype(str)
            df = df[df["text"].str.strip() != ""]

        df["line_group"] = (df["top"] / 19).astype(int)

        found_barcodes = []
        for _, group in df.groupby("line_group"):
            row_words = group.sort_values("left")

            # no need to reverse for english
            row_list = []
            for w in row_words["text"].to_list():
                cleaned_word = self.clean_ocr_text(w)
                if cleaned_word:
                    row_list.append(cleaned_word)
            
            full_line_text = " ".join(row_list)
            # print(f"DEBUG RAW (ENG): {full_line_text}")
            # see if a '-' is near to a number (to skip hyphenated lines)
            if re.match(r'.*\d+\s*-\s*\d+.*', full_line_text):
                # print(f"    Skipping hyphenated line: {full_line_text}")
                continue
            possible_barcodes = re.finditer(r'(?<!\.)\b\d+\b(?!\s*[.%])', full_line_text)
            # print(f"========Scanning line in English for barcodes: {full_line_text}")
            for w in possible_barcodes:
                if w.group(0).isdigit() and len(w.group(0)) > 1 and not w.group(0).startswith('0'):
                    # print(f"    Found English Barcode: {w.group(0)}")
                    found_barcodes.append(w.group(0))
        # print(f"    Detected English Barcodes: {found_barcodes}")
        return found_barcodes
        

    def _process_single_page(self, input_data, is_digital):
        # --- שלב 1: הכנת ה-DataFrame ---
        if is_digital == OCRMode.DIGITAL_PDF:
            df = input_data
        else:
            processed_img = self.enhance_image(input_data)
            if processed_img is None:
                return {"chain name": "", "header": [], "products": []}

            d = pytesseract.image_to_data(
                processed_img,
                lang="heb+eng",
                config=r"--oem 3 --psm 6",
                output_type=Output.DICT,
            )
            df = pd.DataFrame(d)

        if df.empty:
            return {"chain name": "", "header": [], "products": []}

        if "text" in df.columns:
            df["text"] = df["text"].astype(str)
            df = df[df["text"].str.strip() != ""]

        if is_digital == OCRMode.DIGITAL_PDF:
            group_divider = 10
        elif is_digital == OCRMode.SCANNED_PDF:
            group_divider = 30
        else:  # OCRMode.IMAGE
            group_divider = 19

        df["line_group"] = (df["top"] / group_divider).astype(int)

        products = []
        header_lines = []

        header_keywords = ["שם פריט", "ברקוד", "כמות", "מחיר", "ש. פריט", "מידה", "תיאור", "הנחה", "ריחמ", "פריט"]
        global_skip_keywords = [
            "רשת חנויות", "עוסק מורשה", "טלפון", "פקס", "דואר אלקטרוני",
            "חשבונית", "העתק", "לכבוד", "בגין הזמנה", "תאריך", "שעה",
            'סה"כ', "מע\"מ", "מזומן", "אשראי", "חתימה", "לקוח", "עמוד", "דף",
            "סוכן", "אספקה", "חוסרים", "ממחסן", "ויזה", "כאל", "שיק", "בנק", "בבית", "פיקדון"
        ]
        stop_keywords = ["סה\"כ לתשלום", 'סה"כ כולל מע"מ', "כרטיס", "ויזה", "שיק", "מאסטרקארד", "אשראי", "חוסרים", "וויזה", "כאל"]

        chain_name_found = False
        ch = ""
        if is_digital != OCRMode.IMAGE:
            for _, group in df.groupby("line_group"):
                row_words = group.sort_values("left")

                reversed_row_list = []
                if is_digital == OCRMode.SCANNED_PDF:
                    for w in row_words["text"].to_list()[::-1]:
                        cleaned_word = self.clean_ocr_text(w)
                        if cleaned_word:
                            reversed_row_list.append(cleaned_word)
                else:
                    for w in row_words["text"].to_list()[::-1]:
                        w_str = str(w)
                        cleaned_word = (
                            self.clean_ocr_text(w_str[::-1])
                            if not (re.match(r"\b(\d+\.\d{2,3})\b", w_str) or w_str.isdigit())
                            else w_str
                        )
                        if cleaned_word:
                            reversed_row_list.append(cleaned_word)

                full_line_text = " ".join(reversed_row_list)
                # print(f"DEBUG RAW: {full_line_text}")

                if not chain_name_found:
                    ch = self._chain_name_in_line(full_line_text)
                    if ch != "unidentified chain":
                        chain_name_found = True

                if self.table_ended_global:
                    continue

                # --- פתיחת טבלה ---
                if not self.table_started_global:
                    if any(k in full_line_text for k in header_keywords):
                        self.table_started_global = True
                        header_lines.append(full_line_text)
                        continue

                    if re.search(r"\b729\d{9,10}\b", full_line_text):
                        self.table_started_global = True
                    else:
                        header_lines.append(full_line_text)
                        continue

                if any(s in full_line_text for s in stop_keywords):
                    self.table_ended_global = True
                    break

                if any(k in full_line_text for k in global_skip_keywords):
                    header_lines.append(full_line_text)
                    continue

                if len(reversed_row_list) < 5:
                    continue

                # --- barcodes ---
                possible_barcodes = []
                for w in reversed_row_list:
                    if w.isdigit():
                        possible_barcodes.append(w)
                    else:
                        break

                if not possible_barcodes:
                    continue

                barcode = possible_barcodes[1] if len(possible_barcodes) > 1 else possible_barcodes[0]

                if not barcode or len(str(barcode)) < 2:
                    continue

                quantity = 1.0
                unit_type = ""

                def found_kg(line):
                    kgs = ["קג", 'ק"ג', "קילוגרם", "קילוגרמים", "קילו", "גק", 'ג"ק', "םרגוליק", "םימרגוליק", "וליק",
                        'ה"ג', "הג", "גה", 'ג"ה']
                    for w in line:
                        for k in kgs:
                            if k in w:
                                return True
                    return False

                is_kg_found = found_kg(reversed_row_list)

                if not is_kg_found:
                    unit_type = "UNIT"
                    qty_matches = re.findall(r"\b(\d+\.0{1,3})\b", full_line_text)
                    if qty_matches:
                        try:
                            quantity = float(qty_matches[0])
                            if quantity == 0.0:
                                quantity = 1.0
                        except:
                            quantity = 1.0
                else:
                    unit_type = "KG"
                    qty_matches = re.findall(r"\b(\d+\.\d{2,3})\b", full_line_text)
                    if qty_matches:
                        try:
                            quantity = float(qty_matches[0])
                            if quantity == 0.0:
                                quantity = 1.0
                        except:
                            quantity = 1.0

                products.append(
                    {"barcode": barcode, "quantity": quantity, "unit": unit_type, "line": full_line_text}
                )

            return {"chain name": ch, "header": header_lines, "products": products}
        else: # is_digital == OCRMode.IMAGE
            # --- שלב 1: משתנים לאיסוף שורות ---
            raw_product_blocks = [] # רשימה של רשימות (כל פריט הוא רשימת שורות ששייכות למוצר אחד)
            current_block_lines = [] # השורות של המוצר הנוכחי שנצבר
            found_barcodes = self._scan_english_numbers(processed_img)
            
            # רשימת מילים לסינון (רעש)
            line_skip_keywords = [
                "מוגבל", "מבצע", "הנחה", "זיכוי", "לתשלום", "כרטיס", "אשראי", 
                "מסוף", "עסקה", "שיק", "מזומן", "עודף", "חשבונית", "עוסק", "מורשה",
                "טלפון", "פקס", "שעה", "תאריך", "קופאי", "סניף", "ח.פ", "ע.מ", 
                "העתק", "מקור", "סימוכין"
            ]

            # לולאה על השורות הגולמיות מה-OCR
            for _, group in df.groupby("line_group"):
                row_words = group.sort_values("left")

                # ניקוי והכנת השורה
                reversed_row_list = []
                for w in row_words["text"].to_list()[::-1]:
                    cleaned_word = self.clean_ocr_text(w)
                    if cleaned_word:
                        reversed_row_list.append(cleaned_word)
                
                if not reversed_row_list:
                    continue

                # to_print = [f"[{i}] '{w}'" for i, w in enumerate(reversed_row_list)]
                # print(f"DEBUG WORDS: {' | '.join(to_print)}")

                full_line_text = " ".join(reversed_row_list)

                # הדפסה לדיבוג (כדי שתראה מה נכנס)
                # print(f"DEBUG RAW: {full_line_text}")

                if not chain_name_found:
                    ch = self._chain_name_in_line(full_line_text)
                    if ch != "unidentified chain":
                        chain_name_found = True

                # --- 1. סינון רעש אגרסיבי (Skip Logic) ---
                # א. בדיקת מילים אסורות
                if any(skip_word in full_line_text for skip_word in line_skip_keywords):
                    # print(f"    Skipping line (noise detected): {full_line_text}")
                    continue

                # ג. בדיקת סיום קבלה
                if any(s in full_line_text for s in stop_keywords):
                    self.table_ended_global = True
                    # print(f"    Table ended detected by line: {full_line_text}")
                    break

                # --- 2. לוגיקת "המתנה להתחלה" ---
                # מדלגים על הכל עד שרואים כותרת או ברקוד
                if not self.table_started_global:
                    # האם זו כותרת? (קוד פריט, שם פריט...)
                    if any(k in full_line_text for k in header_keywords):
                        self.table_started_global = True
                        # print(f"    Table started detected by line: {full_line_text}")
                        continue # מדלגים על שורת הכותרת עצמה
                    
                    else:
                        # print(f"    Still waiting for table start, skipping line: {full_line_text}")
                        continue # עדיין בהדר/לוגו - דלג

                # --- 3. זיהוי "טריגר" למוצר חדש (Aggregation Logic) ---
                
                is_new_product_start = False
                found_barcodes_in_line = re.finditer(r'(?<!\.)\b\d+\b(?!\s*[.%])', full_line_text)               
                for fb in found_barcodes_in_line:
                    if fb.group(0) in found_barcodes:
                        is_new_product_start = True
                        # print(f"    Detected new product start by barcode: {fb.group(0)} in line: {full_line_text}")
                        break

                # --- 4. בניית הבלוקים --- 
                if is_new_product_start:
                    # אם כבר צברנו שורות של מוצר קודם - נשמור אותן
                    if current_block_lines:
                        raw_product_blocks.append(current_block_lines)
                    
                    # מתחילים מוצר חדש
                    current_block_lines = [full_line_text]
                
                else:
                    if current_block_lines:
                        current_block_lines.append(full_line_text)

            # לא לשכוח את הבלוק האחרון שנשאר ביד בסוף הלולאה
            if current_block_lines:
                raw_product_blocks.append(current_block_lines)


            # ==========================================
            # חלק ב': הלוגיקה שלך (Parsing Logic)
            # ==========================================
            
            final_products_dict = {}

            # print(f"\n--- Starting Custom Parsing on {len(raw_product_blocks)} Blocks ---")

            for block in raw_product_blocks:
                # סינון כותרות בתוך הבלוק
                flag = False
                for hkw in header_keywords:
                    if hkw in " ".join(block):
                        # print(f"  SKIPPING BLOCK (header detected): {' '.join(block)}")
                        flag = True
                        break
                if flag:
                    continue

                # סינון בלוקים שמכילים מילים אסורות
                flag = False
                for gskw in global_skip_keywords:
                    if gskw in " ".join(block):
                        # print(f"  SKIPPING BLOCK (global skip word detected): {' '.join(block)}")
                        flag = True
                        break
                if flag:
                    continue
                
                full_product_string = " ".join(block)
                # print(f"PROCESSING BLOCK: {full_product_string}")
                
                extracted_barcode = None
                extracted_qty = 1.0
                extracted_unit = "UNIT"

                extracted_barcode = None  # אתחול המשתנה

                # --- שלב 1: חיפוש ברקוד ארוך (עדיפות עליונה) ---
                long_bc_iterator = re.finditer(r"\b(729\d{9,10}|\d{6,13})\b", full_product_string)

                for match in long_bc_iterator:
                    candidate = match.group(1)
                    # בדיקה שהברקוד תקין (EAN13)
                    if len(candidate) < 13:
                        candidate = '729' + '0' * (10 - len(candidate)) + candidate
                    if len(candidate) > 13:
                        continue
                    if candidate.isdigit() and self.validate_ean13(candidate):
                        extracted_barcode = candidate
                        break  # מצאנו ברקוד תקין! עוצרים את החיפוש

                # --- שלב 2: חיפוש ברקוד קצר (רק אם לא נמצא ארוך) ---
                if not extracted_barcode:
                    # ה-Regex המעודכן שמסנן מחירים ואחוזים
                    short_bc_iterator = re.finditer(r"(?<!\.)\b(\d{3,6})\b(?!\s*%)(?!\.\d)", full_product_string)

                    for match in short_bc_iterator:
                        candidate = match.group(1)
                        
                        if candidate.isdigit() and not candidate.startswith('0'):
                            extracted_barcode = candidate
                            break

                
                # 2. חילוץ משקל/יחידה
                keywords_pattern = r"(?:יחידה|הדיחי)"
        
                pattern = rf"""
                (            
                    \d+א        | # number צמוד ל-א
                    א\d+        | # א צמוד למספר
                    א\s+\d+     | # א רווח מספר
                    \d+\s+א     | # number רווח א
                    \d+x        | # number צמוד ל-x
                    x\d+        | # x צמוד למספר
                    x\s+\d+     | # x רווח מספר
                    \d+\s+x      # number רווח x
                )
                \s+             # רווח חובה אחרי הצירוף
                {keywords_pattern} # המילה (יחידה/הדיחי)
                """
                match = re.search(pattern, full_product_string, re.VERBOSE | re.IGNORECASE)

                if match:
                    # group(1) contains the word found BEFORE the keyword
                    possible_unit = match.group(1).replace("א", "").replace("x", "").strip()
                    if possible_unit.isdigit():
                        extracted_qty = float(possible_unit)
                    # print(f"Found: {extracted_qty}")
                    

                if any(w in full_product_string for w in['ק"ג', 'ג"ק', "ג'ק", "ק'ג"]):
                # elif "קג" in full_product_string or 'ק"ג' in full_product_string:
                    extracted_unit = "KG"
                # אם יש נקודה עשרונית עם 3 ספרות (0.716) זה בדרך כלל המשקל
                    weight_match = re.search(r"\b(\d+\.\d{3})\b", full_product_string)
                    if weight_match:
                        extracted_qty = float(weight_match.group(1))
                        extracted_unit = "KG"
                     # אם יש יחידה אבל לא מצאנו 3 ספרות, נחפש מספר אחר
                     # ...

                # --- שמירה למילון התוצאות ---
                if extracted_barcode:
                    # טיפול בכפילויות (אם אותו מוצר מופיע פעמיים)
                    if extracted_barcode in final_products_dict:
                        final_products_dict[extracted_barcode]["quantity"] += extracted_qty
                    else:
                        final_products_dict[extracted_barcode] = {
                            "barcode": extracted_barcode,
                            "quantity": extracted_qty,
                            "unit": extracted_unit,
                            "line": full_product_string # שומרים את השורה המלאה לדיבוג
                        }

            # המרה לפורמט הסופי שהפונקציה צריכה להחזיר
            products_list = list(final_products_dict.values())
            

            return {"chain name": ch, "header": [], "products": products_list}

    def _chain_name_in_line(self, line: str) -> str:
        retail_chains_map = {
            "קינג סטור": "King Store",
            "מעיין אלפיים": "Maayan 2000",
            "גוד פארם": "Good Pharm",
            "קרפור": "carrefour",
            "קוויק": "Quik",
            "ביתן אונליין": "Bitan Online",
            "יינות ביתן": "Yeinot Bitan",
            "מגה": "Mega",
            "דור אלון": "Dor Alon",
            "אלונית": "Alonit",
            "וולט": "Wolt",
            "ויקטורי": "victory",
            "זול ובגדול": "Zol VeBegadol",
            "ח. כהן": "H. Cohen",
            "טיב טעם": "tivtaam",
            "מחסני השוק": "mck",
            "חצי חינם": "hazi-hinam",
            "יוחננוף": "yohananof",
            "אושר עד": "osherad",
            "נתיב החסד": "Nativ HaChessed",
            "ברכל": "BarKol",
            "סאלח דבאח": "salachd",
            "סופר ספיר": "Super Sapir",
            "סופר פארם": "Super-Pharm",
            "סיטי מרקט": "citymarket",
            "סטופ מרקט": "Stop Market",
            "עוף והודו ברקת": "Of VeHodu Bareket",
            "פוליצר": "Polizer",
            "יילו": "Yellow",
            "סופר יודה": "Super Yuda",
            "פרשמרקט": "Freshmarket",
            "משנת יוסף": "Mishnat Yosef",
            "קשת טעמים": "keshet",
            "רמי לוי שיווק השקמה": "ramilevi",
            "סופר קופיקס": "Super Cofix",
            "שופרסל": "shufersal",
            "Be": "Be",
            "שוק העיר": "Shouk HaIr",
            "שפע ברכת השם": "Shefa Birkat Hashem",
        }
        for chain in retail_chains_map.keys():
            words = chain.split(' ')
            for word in words:
                if word in line:
                    return retail_chains_map[chain]
        return "unidentified chain"

    def validate_ean13(self, barcode: str) -> bool:
        """
        בודקת האם מחרוזת היא ברקוד EAN-13 תקין.
        :param barcode: הברקוד כמחרוזת (string)
        :return: True אם תקין, False אחרת
        """
        # 1. בדיקות בסיסיות: חייב להיות מחרוזת, אורך 13, ורק מספרים
        if not isinstance(barcode, str) or len(barcode) != 13 or not barcode.isdigit():
            return False

        try:
            # המרה לרשימת מספרים
            digits = [int(d) for d in barcode]
            
            # הפרדה בין הנתונים (12 הראשונים) לספרת הביקורת (האחרונה)
            data_digits = digits[:-1]
            checksum_digit = digits[-1]

            # 2. חישוב הסכום לפי משקלים (Weighting)
            # מיקומים אי זוגיים (1, 3, 5...) מקבלים משקל 1
            # מיקומים זוגיים (2, 4, 6...) מקבלים משקל 3
            # * הערה: בפייתון האינדקס מתחיל ב-0, אז אינדקס זוגי הוא מיקום אי-זוגי ולהפך.
            
            total_sum = 0
            for i, digit in enumerate(data_digits):
                if i % 2 == 0:  # אינדקס 0, 2, 4... (מיקום 1, 3, 5...) -> משקל 1
                    total_sum += digit * 1
                else:           # אינדקס 1, 3, 5... (מיקום 2, 4, 6...) -> משקל 3
                    total_sum += digit * 3

            # 3. חישוב ספרת הביקורת הצפויה
            remainder = total_sum % 10
            if remainder == 0:
                calculated_checksum = 0
            else:
                calculated_checksum = 10 - remainder

            # 4. השוואה
            ret = checksum_digit == calculated_checksum
            return ret

        except Exception:
            return False