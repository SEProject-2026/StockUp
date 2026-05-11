import os
import requests
import gzip
import shutil
import csv
import xml.etree.ElementTree as ET
import sys
import time
import re
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
import urllib3

# Display settings
sys.stdout.reconfigure(encoding='utf-8')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Settings ---
DOWNLOAD_DIR = "update"

# Chain configurations
CHAINS_CONFIG = {
    # === Cerberus group (working fine) ===
    "ramilevi":  {"type": "cerberus", "url": "https://url.publishedprices.co.il", "username": "RamiLevi"},
    "yohananof": {"type": "cerberus", "url": "https://url.publishedprices.co.il", "username": "Yohananof"},
    "tivtaam":   {"type": "cerberus", "url": "https://url.publishedprices.co.il", "username": "TivTaam"},
    "osherad":   {"type": "cerberus", "url": "https://url.publishedprices.co.il", "username": "OsherAd"},
    
    # === Laib group (Victory / Machsanei Hashuk) ===
    "victory":   {"type": "laib", "url": "https://laibcatalog.co.il", "chain_name": "ויקטורי"},
    "mck":       {"type": "laib", "url": "https://laibcatalog.co.il", "chain_name": "מחסני השוק"},
    
    # === Dedicated sites ===
    "carrefour": {"type": "carrefour", "url": "https://prices.carrefour.co.il"},
    "shufersal": {"type": "shufersal", "url": "https://prices.shufersal.co.il/"},
}

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors')
    chrome_options.set_capability("acceptInsecureCerts", True)
    # chrome_options.add_argument("--headless") # Recommended to leave commented out to see the browser working
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def extract_date_from_filename(filename):
    """Extract date from filename for sorting"""
    try:
        match = re.search(r"(202\d{5})", filename) # YYYYMMDD
        if match: return datetime.strptime(match.group(1), "%Y%m%d")
        
        match_alt = re.search(r"(\d{8})", filename) # 8 digits fallback
        if match_alt: return datetime.strptime(match_alt.group(1), "%Y%m%d")
    except: pass
    return datetime(2000, 1, 1)

# ==========================================
# 1. Cerberus Handler
# ==========================================
def handle_cerberus(driver, config):
    base_url = config["url"]
    username = config["username"]
    target_url = f"{base_url}/{username}"
    
    print(f"   -> Connecting to Cerberus ({username})...")
    driver.get(target_url)
    wait = WebDriverWait(driver, 10)
    
    if "login" in driver.current_url.lower() or len(driver.find_elements(By.NAME, "username")) > 0:
        print("   -> Login required...")
        try:
            wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(username)
            driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            wait.until(lambda d: "login" not in d.current_url.lower())
        except: pass

    time.sleep(3)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    candidates = []
    
    for a in soup.find_all('a'):
        href = a.get('href')
        text = a.get_text()
        if (href and "PriceFull" in href and ".gz" in href) or (text and "PriceFull" in text and ".gz" in text):
            clean_href = href if href else text
            if not clean_href.startswith("http"):
                clean_href = f"{base_url}{clean_href}" if clean_href.startswith("/") else f"{base_url}/{clean_href}"
            candidates.append(clean_href)
            
    return candidates

# ==========================================
# 2. Laib Handler (Victory, Machsanei Hashuk) - fixed according to image
# ==========================================
def handle_laib(driver, config):
    url = config["url"]
    chain_name = config["chain_name"]
    
    print(f"   -> Connecting to Laib Catalog ({chain_name})...")
    driver.get(url)
    wait = WebDriverWait(driver, 20)
    
    # 1. Select chain
    print("   -> Selecting Chain...")
    try:
        selects = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "select")))
        chain_selected = False
        for sel in selects:
            if chain_name in sel.text:
                Select(sel).select_by_visible_text(chain_name)
                chain_selected = True
                time.sleep(3) # Wait for sub-lists to load
                break
        
        if not chain_selected and len(selects) > 0:
            Select(selects[0]).select_by_visible_text(chain_name)
            
    except Exception as e:
        print(f"   [!] Error selecting chain: {e}")
        return []

    # 2. Select file type (must select 'Full')
    print("   -> Selecting File Type (Looking for PriceFull)...")
    try:
        # Refresh select list
        selects = driver.find_elements(By.TAG_NAME, "select")
        type_found = False
        
        for sel in selects:
            try:
                s = Select(sel)
                # Iterate through options and check for "full price" indicators
                for opt in s.options:
                    text = opt.text
                    # More precise search
                    if "PriceFull" in text or "מחירים מלא" in text or "קובץ מחירים מלא" in text:
                        s.select_by_visible_text(text)
                        type_found = True
                        print(f"      [V] Selected type: {text}")
                        break
                if type_found: break
            except: continue
            
        if not type_found:
            print("   [!] Could not find 'PriceFull' option. Search results might be partial.")

    except Exception as e:
        print(f"   [!] Error selecting type: {e}")

    # 3. Click search
    print("   -> Clicking Search...")
    try:
        search_btns = driver.find_elements(By.CSS_SELECTOR, "a.btn-primary, input[value='חיפוש'], button")
        clicked = False
        for btn in search_btns:
            if "חיפוש" in btn.text or "חפש" in btn.get_attribute("value"):
                driver.execute_script("arguments[0].click();", btn)
                clicked = True
                break
        if not clicked and search_btns:
            search_btns[0].click()
            
    except Exception as e:
        print(f"   [!] Search click failed: {e}")
            
    print("   -> Waiting for results...")
    time.sleep(5)

    # 4. Strict extraction and filtering (The Guard)
    candidates = []
    links = driver.find_elements(By.XPATH, "//a[contains(@href, '.gz')]")
    
    print(f"   -> Scanning {len(links)} links...")
    for link in links:
        href = link.get_attribute("href")
        
        # === The critical filter ===
        # If the link doesn't contain PriceFull - we don't want it!
        # This will filter out the empty Promo and Price (updates).
        if "PriceFull" not in href:
            continue
            
        candidates.append(href)
        
    print(f"   -> Found {len(candidates)} VALID PriceFull files.")
    return candidates
# ==========================================
# 3. Carrefour Handler (FIXED)
# ==========================================
def handle_carrefour(driver, config):
    url = config["url"]
    print("   -> Connecting to Carrefour...")
    driver.get(url)
    
    wait = WebDriverWait(driver, 20)
    
    try:
        # 1. Select category: PriceFull
        print("   -> Selecting Category 'PriceFull'...")
        
        # Identify the category dropdown.
        # On these sites, it's usually the rightmost select or the one containing the relevant options
        selects = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "select")))
        
        category_select = None
        for sel in selects:
            # Check if this select has a prices option
            try:
                s = Select(sel)
                for opt in s.options:
                    text = opt.text.lower()
                    # Identify by characteristic text
                    if "pricefull" in text or "קבצי מחירים" in text:
                        category_select = s
                        break
            except: continue
            if category_select: break
        
        if category_select:
            # Select the correct option
            found = False
            for opt in category_select.options:
                text = opt.text.lower()
                if "pricefull" in text or "קבצי מחירים" in text:
                    category_select.select_by_visible_text(opt.text)
                    found = True
                    break
            
            if not found and len(category_select.options) > 1:
                category_select.select_by_index(1) # Default
                
            print("   -> Category selected. Waiting for auto-refresh...")
            time.sleep(5) # Wait for auto-table load
        else:
            print("   [!] Could not locate Category dropdown. Scanning page anyway...")

        # 2. Extract links from the table
        # Search for download links (usually an icon, but the href exists)
        print("   -> Scanning results...")
        
        # Search for table rows
        rows = driver.find_elements(By.CSS_SELECTOR, "tr")
        candidates = []
        
        for row in rows:
            try:
                # Check if the row contains an indication of a prices file and GZ
                row_text = row.text
                if "PriceFull" in row_text and ".gz" in row_text:
                    # Find the link inside the row
                    links = row.find_elements(By.TAG_NAME, "a")
                    for link in links:
                        href = link.get_attribute("href")
                        if href and ".gz" in href:
                            candidates.append(href)
                            break # One link per row is enough
            except: pass

        # If we didn't find it the smart way, we will try to "brute force" find any GZ link on the page
        if not candidates:
            links = driver.find_elements(By.XPATH, "//a[contains(@href, '.gz')]")
            for link in links:
                href = link.get_attribute("href")
                if "PriceFull" in href or "PriceFull" in link.text: # Basic filter
                    candidates.append(href)

        print(f"   -> Found {len(candidates)} files.")
        return candidates

    except Exception as e:
        print(f"   [!] Carrefour error: {e}")
        return []

# ==========================================
# 4. Shufersal Handler (FIXED & ROBUST)
# ==========================================
def handle_shufersal(driver, config):
    url = config["url"]
    print("   -> Connecting to Shufersal...")
    driver.get(url)
    
    # זמן המתנה ארוך יותר לאתר של שופרסל
    wait = WebDriverWait(driver, 20)
    
    try:
        # 1. Select category: "PricesFull"
        print("   -> Selecting Category...")
        # Wait for the Select to exist and be clickable
        cat_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "select[id*='ddlCategory']")))
        cat_select = Select(cat_element)
        
        found_cat = False
        for opt in cat_select.options:
            # Search for "price files" or "PricesFull"
            # We added conditions to catch the correct option for sure
            text = opt.text.lower()
            if "pricesfull" in text or ("מחיר" in text and "מלא" in text):
                cat_select.select_by_visible_text(opt.text)
                found_cat = True
                break
        
        if not found_cat:
            # If we didn't find an exact text, we will select by index (usually 1 or 2 is prices)
            print("   -> Exact category text not found, trying index 1...")
            if len(cat_select.options) > 1:
                cat_select.select_by_index(1)

        # 2. Select store: All
        # Important: After selecting a category, the stores HTML refreshes (PostBack). We must wait.
        time.sleep(4) 
        
        print("   -> Selecting Store...")
        store_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "select[id*='ddlStore']")))
        store_select = Select(store_element)
        
        # We will try to select the first option that isn't "Select store" (usually "All stores")
        if len(store_select.options) > 0:
            store_select.select_by_index(0) 

        # 3. Click search 
        print("   -> Clicking Search...")
        
        # The fix: We removed the word input from the selector. Now it will also find <a> or <button> elements
        try:
            search_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[id*='btnSearch']")))
            # Use JavaScript to perform the click (bypasses hiding or blocking issues)
            driver.execute_script("arguments[0].click();", search_btn)
        except Exception as click_error:
            print(f"   [!] JS Click failed, trying Enter key: {click_error}")
            # Backup attempt: Sending ENTER key to the stores box
            store_element.send_keys(u'\ue007') # Keys.ENTER
        
        print("   -> Waiting for results table...")
        # Wait for the table to update (identified by new links or table appearing)
        time.sleep(5)
        
        # 4. Extract the link
        # Collect all links ending in gz and containing PriceFull
        links = driver.find_elements(By.XPATH, "//a[contains(@href, 'PriceFull') and contains(@href, '.gz')]")
        
        candidates = []
        for link in links:
            href = link.get_attribute("href")
            if href:
                candidates.append(href)
        
        print(f"   -> Found {len(candidates)} files.")
        return candidates

    except Exception as e:
        print(f"   [!] Shufersal error details: {str(e)}")
        # Save screenshot to folder to understand what happened
        try: driver.save_screenshot("debug_shufersal_error.png")
        except: pass
        return []
# ==========================================
# Main & Download Logic
# ==========================================
def convert_xml_to_csv(xml_file, chain_key):
    csv_file = os.path.join(DOWNLOAD_DIR, f"{chain_key}.csv")
    print(f"   -> Converting to CSV (Fixed): {csv_file}...")
    
    row_count = 0
    
    try:
        # Use iterparse
        context = ET.iterparse(xml_file, events=("end",))
        
        with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            # Define the columns we are looking for
            cols = ["ItemCode", "ItemName", "ManufacturerName", "ItemPrice", "UnitOfMeasure", "QtyInPackage"]
            writer.writerow(cols)
            
            for event, elem in context:
                # The universal logic:
                # We don't check the main tag name (Item/Product),
                # but we check if it has "children" with the correct names.
                
                row_data = {}
                has_code = False
                
                # Scan the children of the current element
                for child in elem:
                    # Clean Namespace from the child's name (e.g. {http://...}ItemCode -> ItemCode)
                    tag_clean = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                    
                    # Normalize different names between chains
                    if tag_clean == "Quantity": tag_clean = "QtyInPackage"
                    
                    # Save the info if it's relevant
                    if tag_clean in cols:
                        row_data[tag_clean] = child.text
                        if tag_clean == "ItemCode":
                            has_code = True
                
                # If we found ItemCode, we write the row
                if has_code:
                    writer.writerow([
                        row_data.get("ItemCode", ""),
                        row_data.get("ItemName", ""),
                        row_data.get("ManufacturerName", ""),
                        row_data.get("ItemPrice", "0.00"),
                        row_data.get("UnitOfMeasure", ""),
                        row_data.get("QtyInPackage", "")
                    ])
                    row_count += 1

                    elem.clear()
                    
        print(f"   -> Conversion complete. Rows written: {row_count}")
        return True

    except Exception as e:
        print(f"   -> Error converting XML: {e}")
        return False

def download_file(url, chain_key, cookies=None, user_agent=None):
    session = requests.Session()
    if cookies:
        for cookie in cookies:
            session.cookies.set(cookie['name'], cookie['value'])
    if user_agent:
        session.headers.update({"User-Agent": user_agent})

    try:
        local_gz = os.path.join(DOWNLOAD_DIR, f"{chain_key}_temp.xml.gz")
        local_xml = os.path.join(DOWNLOAD_DIR, f"{chain_key}_raw.xml")
        
        print(f"   -> Downloading file from: {url}")
        with session.get(url, stream=True, verify=False) as r:
            r.raise_for_status()
            with open(local_gz, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        print(f"   -> Extracting...")
        with gzip.open(local_gz, 'rb') as f_in:
            with open(local_xml, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        success = convert_xml_to_csv(local_xml, chain_key)
        
        if os.path.exists(local_gz): os.remove(local_gz)
        if success and os.path.exists(local_xml): os.remove(local_xml)
        
        print(f"[V] SUCCESS: {chain_key}")
        
    except Exception as e:
        print(f"[X] Download failed for {chain_key}: {e}")

def process_chain(chain_key, config):
    print(f"\nProcessing Chain: {chain_key}...")
    driver = setup_driver()
    candidates = []
    
    try:
        c_type = config["type"]
        
        if c_type == "cerberus":
            candidates = handle_cerberus(driver, config)
        elif c_type == "laib":
            candidates = handle_laib(driver, config)
        elif c_type == "carrefour":
            candidates = handle_carrefour(driver, config)
        elif c_type == "shufersal":
            candidates = handle_shufersal(driver, config)
            
        if not candidates:
            print(f"   [!] No files found for {chain_key}")
            return

        print(f"   -> Found {len(candidates)} files. Selecting newest...")
        
        dated_files = []
        for url in candidates:
            d = extract_date_from_filename(url)
            dated_files.append((url, d))
            
        dated_files.sort(key=lambda x: x[1], reverse=True)
        
        best_url = dated_files[0][0]
        best_date = dated_files[0][1]
        
        print(f"   -> Selected: {os.path.basename(best_url)}")
        print(f"   -> Date: {best_date}")
        
        cookies = driver.get_cookies()
        user_agent = driver.execute_script("return navigator.userAgent;")
        driver.quit()
        
        download_file(best_url, chain_key, cookies, user_agent)
        
    except Exception as e:
        print(f"   [X] Error in processing loop: {e}")
        if driver: driver.quit()

def main():
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
        
    print("Starting Ultimate Price Update (Fixed Selectors)...")
    print("-" * 50)
    
    for key, config in CHAINS_CONFIG.items():
        process_chain(key, config)
        
    print("\n" + "-" * 50)
    print("All tasks completed.")

if __name__ == "__main__":
    main()