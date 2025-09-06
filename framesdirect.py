# IMPORTING IMPORTANT LIBRARIES
import time
import csv
import json
import os
import re 
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException


# ---------------------------------------------
# STEP 1: CONFIGURATION OF SCRAPER-CLIENT KEY PARAMETER
# ---------------------------------------------

# Base URL
base_url = "https://www.framesdirect.com"

# Safety stop so that scraper does not run forever when there is endless next page looping
MAX_PAGES = 10  

# Checkpoint file
CHECKPOINT_FILE = "checkpoint.json"



# CHECKPOINT HANDLING

# Load last scraped page number from checkpoint.json (if exists)
if os.path.exists(CHECKPOINT_FILE):
    with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
        checkpoint = json.load(f)
    start_page = checkpoint.get("last_page", 1) + 1
    print(f"Resuming from page {start_page}...")
else:
    start_page = 1
    print("Starting fresh from page 1...")



# SELENIUM & WEBDRIVER SETUP

# Setup Chrome WB options
chrome_options = Options()
chrome_options.add_argument("--headless")   
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")     
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.265 Safari/537.36")
driver = webdriver.Chrome(options=chrome_options)
print("done setting up..")

# Installing Chrome WebDriver
print("Installing Chrome WD")
service = Service(ChromeDriverManager().install())
print("Final Setup")
driver = webdriver.Chrome(service=service, options=chrome_options)
print("Done")


# --------------------------------
# STEP 2: DATA FETCHING/EXTRACTION
# --------------------------------

# Defining & Lauching Start URL
start_url = f"{base_url}/eyeglasses/?p={start_page}&type=pagestate"
driver.get(start_url)

# Storage for extracted products & extraction page track
eye_glasses_data = []
page_count = 0

while True:
    page_count += 1
    current_page = start_page + page_count - 1
    print(f"\n--- Scraping page {current_page} ---")

    # === Wait for product tiles to load ===
    try:
        print("Waiting for product tiles to load...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "prod-holder"))
        )
        print("Done...Proceed to parse the data")
    except TimeoutException as e:
        print(f"Error waiting for {driver.current_url}: {e}")
        driver.quit()
        print("Browser closed due to timeout")
        break

    # PARSE EXTRACTED DATA WITH BEAUTIFUL SOUP & FILTER ALL PRODUCT-HOLDER CLASS
    soup = BeautifulSoup(driver.page_source, "html.parser")
    product_tiles = soup.find_all("div", class_="prod-holder")
    print(f"Found {len(product_tiles)} products on this page")

    
    # EXTRACT NEEDED PRODUCT DATA

    for tile in product_tiles:
        # Extract Brand information
        product_brand = tile.find("span", class_="prodBrand d-none")
        brand = product_brand.get_text(strip=True) if product_brand else None

        # Extract Name information
        product_name = tile.find("div", class_="product_name")
        name = product_name.get_text(strip=True) if product_name else None

        # Extract Prices infomation
        product_prices = tile.find("div", class_="prod-bot")
        if product_prices:
            # Original Price
            original_price_tag = product_prices.find("div", class_="prod-catalog-retail-price")
            if original_price_tag:
                try:
                    original_price = float(original_price_tag.get_text(strip=True).replace("$", "").replace(",", ""))
                except ValueError:
                    original_price = None
            else:
                original_price = None

            # Current Price
            current_price_tag = product_prices.find("div", class_="prod-aslowas")
            if current_price_tag:
                try:
                    current_price = float(current_price_tag.get_text(strip=True).replace("$", "").replace(",", ""))
                except ValueError:
                    current_price = None
            else:
                current_price = None

            # Discount
            discount_tag = product_prices.find("div", class_="frame-discount size-11")
            if discount_tag:
                discount_text = discount_tag.get_text(strip=True)
                match = re.search(r"(\d+)", discount_text)  # extract digits
                discount_applied = int(match.group(1)) if match else None
            else:
                discount_applied = None


        else:
            original_price = current_price = discount_applied = None
            # Automatically applies missing value, if the product info is not available.

        
        # ---------------------------
        # STEP 3: SAVE EXTRACTED DATA
        # ----------------------------
        
        # === Store all extracted values in a dictionary ===
        data = {
            "Brand": brand,
            "Product_Name": name,
            "Former_Price": original_price,
            "Current_Price": current_price,
            "Discount": discount_applied
        }
        
        # === Append saved product's dictionary to the data storage list. ===
        eye_glasses_data.append(data)

    # === Save checkpoint ===
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_page": current_page}, f)

    # === Stop if max pages reached ===
    if page_count >= MAX_PAGES:
        print(f"Reached MAX_PAGES ({MAX_PAGES}). Stopping.")
        break

    # === Pagination (URL-based) ===
    next_btn = soup.find("a", {"aria-label": "next page"})
    if next_btn and "href" in next_btn.attrs:
        next_url = next_btn["href"]
        if not next_url.startswith("http"):
            next_url = base_url + next_url
        print(f"Going to next page: {next_url}")
        driver.get(next_url)
        time.sleep(10)  # allow page to load
    else:
        print("No more pages found. Stopping.")
        break

# === Save results ===
if eye_glasses_data:
    # save to CSV
    column_name = eye_glasses_data[0].keys()
    with open("framesdirectdotcom_data_updated.csv", mode="a", newline="", encoding="utf-8") as csv_file:
        dict_writer = csv.DictWriter(csv_file, fieldnames=column_name)
        if csv_file.tell() == 0:  # write header only if file is empty
            dict_writer.writeheader()
        dict_writer.writerows(eye_glasses_data)
    print(f"Appended {len(eye_glasses_data)} records to CSV")

    # save to JSON
    if os.path.exists("framesdirectdotcom.json"):
        with open("framesdirectdotcom.json", "r", encoding="utf-8") as f:
            existing_data = json.load(f)
    else:
        existing_data = []

    existing_data.extend(eye_glasses_data)
    with open("framesdirectdotcom_update.json", mode="w", encoding="utf-8") as json_file:
        json.dump(existing_data, json_file, indent=4)
    print(f"Saved {len(eye_glasses_data)} new records to JSON")
else:
    print("No data collected.")

# close the browser
driver.quit()
print("Enf of Extraction")
