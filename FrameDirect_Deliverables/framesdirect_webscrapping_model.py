
import os
import re
import csv
import json
import time
from datetime import datetime
import psycopg2
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager


# -----------------------------
# CONFIGURATION & GLOBALS
# -----------------------------
BASE_URL = "https://www.framesdirect.com"
MAX_PAGES = 10
CHECKPOINT_FILE = "checkpoint.json"
OUTPUT_FOLDER = r"C:\Users\Admin\Documents\Smart_Eyewear_Choices\FrameDirect_Deliverables"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
CSV_PATH = os.path.join(OUTPUT_FOLDER, "framesdirectdotcom_data.csv")
JSON_PATH = os.path.join(OUTPUT_FOLDER, "framesdirectdotcom.json")


# -----------------------------
# FUNCTIONS
# -----------------------------

def setup_webdriver():
    """Sets up and returns a configured Selenium WebDriver."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.265 Safari/537.36"
    )
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    print("✅ Selenium WebDriver setup complete.")
    return driver


def load_checkpoint():
    """Load the last scraped page number from checkpoint file."""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            checkpoint = json.load(f)
        start_page = checkpoint.get("last_page", 1) + 1
        print(f"Resuming from page {start_page}...")
    else:
        start_page = 1
        print("Starting fresh from page 1...")
    return start_page


def extract_product_data(html_source):
    """Parses the HTML source and extracts product data."""
    soup = BeautifulSoup(html_source, "html.parser")
    product_tiles = soup.find_all("div", class_="prod-holder")
    products = []

    for tile in product_tiles:
        brand_tag = tile.find("span", class_="prodBrand d-none")
        brand = brand_tag.get_text(strip=True) if brand_tag else None

        name_tag = tile.find("div", class_="product_name")
        name = name_tag.get_text(strip=True) if name_tag else None

        prices = tile.find("div", class_="prod-bot")
        if prices:
            # Original Price
            orig_price_tag = prices.find("div", class_="prod-catalog-retail-price")
            try:
                original_price = float(orig_price_tag.get_text(strip=True).replace("$", "").replace(",", "")) if orig_price_tag else None
            except ValueError:
                original_price = None

            # Current Price
            curr_price_tag = prices.find("div", class_="prod-aslowas")
            try:
                current_price = float(curr_price_tag.get_text(strip=True).replace("$", "").replace(",", "")) if curr_price_tag else None
            except ValueError:
                current_price = None

            # Discount
            discount_tag = prices.find("div", class_="frame-discount size-11")
            if discount_tag:
                match = re.search(r"(\d+)", discount_tag.get_text(strip=True))
                discount = int(match.group(1)) if match else None
            else:
                discount = None
        else:
            original_price = current_price = discount = None

        products.append({
            "Brand": brand,
            "Product_Name": name,
            "Former_Price": original_price,
            "Current_Price": current_price,
            "Discount": discount
        })

    print(f"✅ Extracted {len(products)} products from this page")
    return products


def update_checkpoint(page_number):
    """Update checkpoint file with last scraped page."""
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_page": page_number}, f)
    print(f"Checkpoint updated: last_page = {page_number}")


def save_data_to_files(data):
    """Save extracted data to CSV and JSON."""
    if not data:
        print("⚠ No data collected. Nothing saved.")
        return

    # Save CSV
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, "a", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=data[0].keys())
            writer.writerows(data)
    else:
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    print(f"✅ Saved {len(data)} records to CSV")

    # Save JSON
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
        existing_data.extend(data)
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=4)
    else:
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    print(f"✅ Saved {len(data)} records to JSON")


def save_data_to_postgres(data):
    """Save extracted data to PostgreSQL."""
    if not data:
        print("⚠ No data collected. Nothing saved to PostgreSQL.")
        return

    try:
        conn = psycopg2.connect(
            dbname="EyeWearChoices_DB",
            user="postgres",
            password="Eng0802097@",
            host="localhost",
            port="5432"
        )
        cur = conn.cursor()

        for product in data:
            cur.execute("""
                INSERT INTO framesdirect.eyewear_products
                (brand, product_name, former_price, current_price, discount, scraped_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                product["Brand"],
                product["Product_Name"],
                product["Former_Price"],
                product["Current_Price"],
                product["Discount"],
                datetime.now()
            ))

        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ Saved {len(data)} records to PostgreSQL")
    except Exception as e:
        print(f"❌ Error saving to PostgreSQL: {e}")


def scrape_framesdirect():
    """Main scraping workflow."""
    driver = setup_webdriver()
    start_page = load_checkpoint()
    all_data = []
    page_count = 0

    try:
        for page_count in range(MAX_PAGES):
            current_page = start_page + page_count
            url = f"{BASE_URL}/eyeglasses/?p={current_page}&type=pagestate"
            print(f"\n--- Scraping page {current_page}: {url} ---")
            driver.get(url)

            try:
                WebDriverWait(driver, 60).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "prod-holder"))
                )
            except TimeoutException:
                print(f"❌ Timeout waiting for {url}")
                break

            page_data = extract_product_data(driver.page_source)
            all_data.extend(page_data)
            update_checkpoint(current_page)

            # Look for "next page"
            soup = BeautifulSoup(driver.page_source, "html.parser")
            next_btn = soup.find("a", {"aria-label": "next page"})
            if not next_btn or "href" not in next_btn.attrs:
                print("No more pages. Stopping.")
                break

            page_count += 1
            time.sleep(5)

        # Save final collected data
        save_data_to_files(all_data)
        save_data_to_postgres(all_data)

    finally:
        driver.quit()
        print("✅ Scraping complete. Browser closed.")


# -----------------------------
# RUN SCRIPT
# -----------------------------
if __name__ == "__main__":
    scrape_framesdirect()
