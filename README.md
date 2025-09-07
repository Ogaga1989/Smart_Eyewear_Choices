# Smart_Eyewear_Choices

## Overview

This Python project is a web scraper that extracts eyeglasses data from [FramesDirect](https://www.framesdirect.com) in a bid to automating eyewear choices. It collects information on product brand, name, original price, current price, and discount and stores it in both CSV and JSON formats.

## Features

* **Headless Chrome Scraping:** Uses Selenium in headless mode.
* **Dynamic Content Handling:** Waits for `prod-holder` elements ensuring JavaScript-rendered products are fully loaded.
* **Data Extraction:** Brand, Product Name, Former Price, Current Price, and numeric Discount.
* **URL-based Pagination:** Automatically navigates pages until last page or `MAX_PAGES` limit.
* **Resumable Scraping:** Checkpoint system to resume from last scraped page.
* **Data Storage:** Appends results to CSV and JSON to preserve previous runs.

## Requirements

* Python 3.7+
* Packages: `selenium`, `beautifulsoup4`, `pandas`
* Chrome browser and matching ChromeDriver

Install packages with:

```bash
pip install selenium beautifulsoup4 pandas
```

## Usage

1. Ensure `chromedriver` is installed and matches your Chrome version.
2. Run the scraper:

```bash
python framesdirect_scraper.py
```

3. Scraped data will be saved in `framesdirectdotcom_data.csv` and `framesdirectdotcom.json`.
4. If interrupted, the scraper will resume automatically using `checkpoint.json`.

## Customization

* **MAX\_PAGES:** Set the number of pages to scrape per run in the script.
* **Window Size:** Adjust `--window-size` in Chrome options if needed for responsive layouts.

## Viewing Data

```python
import pandas as pd

df = pd.read_csv("framesdirectdotcom_data.csv")
print(df.head())
```

## Notes

* Ensure internet connectivity during scraping.
* The scraper may need updates if FramesDirect changes site structure.
* Avoid excessive requests to prevent being blocked.

## License

This project is open-source and free to use for personal or educational purposes.

