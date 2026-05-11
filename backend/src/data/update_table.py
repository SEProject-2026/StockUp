import os
import glob
import pandas as pd
import re
from datetime import datetime
from supabase import create_client, Client

# --- Configuration ---
# Replace with your actual Supabase project credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

UPDATE_DIR = "update"
TABLE_NAME = "catalog_items" 

TRUSTED_GLOBAL_SOURCES = ["shufersal", "ramilevi", "carrefour", "victory", "tivtaam", "osherad", "yohananof", "mck"]
CHAIN_MAP = {"mck_online": "mck"}

# =========================================
# Category Logic
# =========================================
FRIDGE, FREEZER, PANTRY, CLEANING, OTHER = "fridge", "freezer", "pantry", "cleaning", "Other"

EXACT_WORDS = {
    FREEZER: ["גידרון"],
    FRIDGE: ["תנובה", "דנונה", "טרה", "יטבתה", "טרי", "מ.לסר", "ירק", "יופלה"],
    CLEANING: ["קולגייט", "ליסטרין"],
    PANTRY: ["בחומץ", "פסטה", "אטריות", "עוגיות", "חטיף", "תה", "חליטה"],
}

SUBSTRINGS = {
    CLEANING: ["ניקוי", "מנקה", "חומר ניקוי", "פיירי", "אקונומיקה", "כלור", "מסיר שומנים", "כביסה", "שמפו", "סבון", "חיתולים", "מגבונים"],
    FREEZER: ["קפוא", "קפואה", "גלידת", "גלידה", "בורקס", "ג'חנון", "מלאווח", "בצק", "נאגטס", "המבורגר"],
    FRIDGE: ["יוגורט", "אשל", "גבינת", "גבינה", "קוטג", "שמנת", "חמאה", "ביצים", "פסטרמה", "נקניק", "סלט", "חסה", "עגבניה"],
    PANTRY: ["אורז", "פסטה", "קמח", "רטב", "רוטב", "שמן", "מלח", "סוכר", "שימורים", "טונה", "שוקולד", "קפה", "לחם", "אגוזים"],
}

def normalize(text):
    text = (text or "").lower().strip()
    text = re.sub(r"[^\w\s\u0590-\u05FF]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def guess_category(name):
    txt = normalize(name)
    scores = {FRIDGE: 0, FREEZER: 0, PANTRY: 0, CLEANING: 0}
    for cat, words in EXACT_WORDS.items():
        for w in words:
            pattern = rf"(^|[^\w\u0590-\u05FF]){re.escape(normalize(w))}([^\w\u0590-\u05FF]|$)"
            if re.search(pattern, txt): scores[cat] += 2
    for cat, words in SUBSTRINGS.items():
        for w in words:
            if normalize(w) in txt: scores[cat] += 1
    best_score = max(scores.values())
    if best_score == 0: return OTHER
    tied = [cat for cat, sc in scores.items() if sc == best_score]
    for cat in [CLEANING, FREEZER, FRIDGE, PANTRY]:
        if cat in tied: return cat
    return OTHER

def clean_product_name(name):
    if not name: return ""
    clean = str(name).replace("*", "").replace("!", "").replace("-", " ")
    garbage_words = ["מבצע", "חיסול", "בלעדי", "חדש", "במבצע", "מארז חיסכון"]
    for word in garbage_words:
        clean = clean.replace(word, "")
    return " ".join(clean.split())

def analyze_barcode_identity(barcode_str):
    if not barcode_str: return False, ""
    code = str(barcode_str).strip()
    if len(code) < 5: return False, code
    if code.startswith('000'): return False, str(int(code))
    if code.startswith('7290000'):
        try:
            val = int(code[3:])
            if val < 10000: return False, str(val)
        except: pass 
    return True, code

def process_and_upload():
    csv_files = glob.glob(os.path.join(UPDATE_DIR, "*.csv"))
    
    for file_path in csv_files:
        file_key = os.path.splitext(os.path.basename(file_path))[0]
        chain_name = CHAIN_MAP.get(file_key, file_key)
        print(f"Processing {chain_name}...")
        
        df = pd.read_csv(file_path, dtype={'ItemCode': str}).drop_duplicates(subset=['ItemCode'], keep='first')
        df.rename(columns={'ItemCode': 'Barcode'}, inplace=True)
        
        existing_data = supabase.table(TABLE_NAME).select("*").eq("Chain", chain_name).execute()
        db_products = {row['Barcode']: row for row in existing_data.data}
        db_names = {row['ItemName']: row['Barcode'] for row in existing_data.data}

        final_batch = []
        barcodes_to_delete = []

        for _, row in df.iterrows():
            is_global, clean_code = analyze_barcode_identity(row['Barcode'])
            if not clean_code: continue
            
            csv_name = clean_product_name(row.get('ItemName', ''))
            if not csv_name: continue

            # Swap logic
            if not is_global and csv_name in db_names:
                old_code = db_names[csv_name]
                if old_code != clean_code: barcodes_to_delete.append(old_code)

            new_manufacturer = str(row.get('ManufacturerName', '')) if pd.notna(row.get('ManufacturerName')) else ""
            target_chain = "GLOBAL" if (is_global and chain_name in TRUSTED_GLOBAL_SOURCES) else chain_name

            if clean_code in db_products:
                db_row = db_products[clean_code]
                final_name = db_row.get('ItemName')
                category = db_row.get('SuggestedStorageCategory')
                avg_weight = db_row.get('AverageWeight', 0)
                sample_size = db_row.get('SampleSize', 0)
                last_update = datetime.now().isoformat()
            else:
                final_name = csv_name
                category = guess_category(final_name)
                avg_weight = 0
                sample_size = 0
                last_update = datetime.now().isoformat()

            final_batch.append({
                "Chain": target_chain,
                "Barcode": clean_code,
                "ItemName": final_name,
                "ManufacturerName": new_manufacturer,
                "LastUpdate": last_update,
                "SuggestedStorageCategory": category,
                "AverageWeight": avg_weight,
                "SampleSize": sample_size
            })

        if barcodes_to_delete:
            for i in range(0, len(barcodes_to_delete), 500):
                supabase.table(TABLE_NAME).delete().eq("Chain", chain_name).in_("Barcode", barcodes_to_delete[i:i+500]).execute()

        if final_batch:
            for i in range(0, len(final_batch), 1000):
                supabase.table(TABLE_NAME).upsert(final_batch[i:i+1000]).execute()
            print(f"   Done: {len(final_batch)} items updated/added.")
        else:
            print(f"   No technical changes for {chain_name}.")

if __name__ == "__main__":
    process_and_upload()