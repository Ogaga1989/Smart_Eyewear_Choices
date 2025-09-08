# Smart_Eyewear_Choices

## Overview

This Python project is a **web scraper** that extracts eyeglasses data from [FramesDirect](https://www.framesdirect.com) to automate eyewear product collection. It gathers information on **brand, product name, former price, current price, and discount**. Data is saved in **CSV**, **JSON**, and also automatically loaded into a **PostgreSQL database** for analytics.

---

## Features

* **Headless Chrome Scraping:** Uses Selenium in headless mode for efficiency.  
* **Dynamic Content Handling:** Waits for `prod-holder` elements so JavaScript-rendered products are fully loaded.  
* **Data Extraction:** Collects Brand, Product Name, Former Price, Current Price, and numeric Discount.  
* **URL-based Pagination:** Automatically navigates product pages until the last page or a `MAX_PAGES` limit.  
* **Resumable Scraping:** Checkpoint system (`checkpoint.json`) resumes from last scraped page.  
* **Data Storage:**  
  - Appends new results to CSV (`framesdirectdotcom_data.csv`).  
  - Extends JSON file (`framesdirectdotcom.json`).  
  - Inserts into PostgreSQL (`framesdirect.eyewear_products`) with a timestamp (`scraped_at`).  
* **Error Handling:** Handles timeouts, missing values, and avoids infinite page loops.  

---

## Project Structure

FramesDirect-Scraper/
├── framesdirect.py          # Main scraper script
├── checkpoint.json          # Last scraped page info
├── framesdirectdotcom_data.csv
├── framesdirectdotcom.json
└── README.md
└── requirement.txt          # what is needed to be installed


## Architecture Diagram

      ┌───────────────────┐
      │  FramesDirect.com │
      └─────────┬─────────┘
                │
        (Selenium + BS4)
                │
      ┌─────────▼─────────┐
      │ Data Extraction    │
      │ - Brand            │
      │ - Product Name     │
      │ - Former Price     │
      │ - Current Price    │
      │ - Discount         │
      └─────────┬─────────┘
                │
 ┌──────────────┼──────────────┐
 │              │              │
 ┌────▼────┐ ┌─────▼─────┐ ┌─────▼─────┐
│ CSV │ │ JSON │ │ PostgreSQL │
│ Storage │ │ Storage │ │ Warehouse │
└─────────┘ └───────────┘ └───────────┘ 


## Requirements
* Python 3.7+  
* Chrome browser (latest)  
* PostgreSQL installed and running  

### Install dependencies

It’s recommended to use a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate    # Windows
source venv/bin/activate # Mac/Linux

# Install required packages from requirements.txt:
pip install -r requirements.txt

# Or manually:

pip install selenium beautifulsoup4 psycopg2-binary webdriver-manager


DATABASE SETUP

1. Create the database:

CREATE DATABASE "EyeWearChoices_DB";

2. Create schema and table inside the database:

CREATE SCHEMA framesdirect;

CREATE TABLE framesdirect.eyewear_products (
    id SERIAL PRIMARY KEY,
    brand TEXT,
    product_name TEXT,
    former_price NUMERIC,
    current_price NUMERIC,
    discount INTEGER,
    scraped_at TIMESTAMP DEFAULT NOW()
);

3. Update credentials in framesdirect.py:
conn = psycopg2.connect(
    dbname="EyeWearChoices_DB",
    user="postgres",
    password="your_password",
    host="localhost",
    port="5432"
)


USAGE

Run the scraper on bash:

python framesdirect.py

* Data will be saved into:
  * CSV → FrameDirect_Deliverables/framesdirectdotcom_data.csv
  * JSON → FrameDirect_Deliverables/framesdirectdotcom.json
  * PostgreSQL → framesdirect.eyewear_products
* If stopped, the scraper resumes automatically from checkpoint.json.
* To restart from page 1, delete checkpoint.json.


CUSTOMISATION

* MAX_PAGES: Limit the maximum number of pages per run.

* Window Size: Adjust --window-size Chrome option for layout handling.

* Delay Between Pages: Default is time.sleep(30) for stability; can be changed.


VIEWING DATA

In Python (pandas):

import pandas as pd
df = pd.read_csv("FrameDirect_Deliverables/framesdirectdotcom_data.csv")
print(df.head())

In PostgreSQL:

SELECT * FROM framesdirect.eyewear_products LIMIT 10;


CHECKING AND REMOVING DUPLICATES

In Python:
import pandas as pd

df = pd.read_csv("FrameDirect_Deliverables/framesdirectdotcom_data.csv")
duplicates = df[df.duplicated()]
print(duplicates)

# Remove duplicates and save back
df = df.drop_duplicates()
df.to_csv("FrameDirect_Deliverables/framesdirectdotcom_data.csv", index=False)


In PostgreSQL:

-- Check duplicates
SELECT brand, product_name, COUNT(*)
FROM framesdirect.eyewear_products
GROUP BY brand, product_name
HAVING COUNT(*) > 1;

-- Remove duplicates (keep latest)
DELETE FROM framesdirect.eyewear_products a
USING framesdirect.eyewear_products b
WHERE a.id < b.id
  AND a.brand = b.brand
  AND a.product_name = b.product_name;


TROUBLESHOOTING

1. Timeout Errors

If you see:
selenium.common.exceptions.TimeoutException: Message: timeout
The page may be loading slowly.

Fix: Increase the wait time in:
WebDriverWait(driver, 60)
to a higher value (e.g., 120)

2. PostgreSQL Insert Errors

If you see:

psycopg2.errors.UndefinedTable: relation "framesdirect.eyewear_products" does not exist


Fix: Ensure schema and table are created as described in Database Setup.

3. ChromeDriver Issues

If Selenium cannot start Chrome:

selenium.common.exceptions.SessionNotCreatedException: 
Message: This version of ChromeDriver only supports Chrome version XX


Fix: Update Chrome and ChromeDriver in bash:
pip install -U webdriver-manager


4. Restarting Scraping from Page 1

Delete the checkpoint.json file to reset progress and scrape from the first page again.

5. No Data Appearing

If CSV/JSON are empty:

Ensure internet connection is stable.

Verify that FramesDirect hasn’t changed the prod-holder class.


NOTES

* Ensure internet connectivity during scraping.

* Site structure changes may require updates to the scraper.

* Avoid excessive requests to prevent being blocked.

* checkpoint.json ensures resumability between runs.


LICENSE

This project is open-source and free to use for personal or educational purposes.