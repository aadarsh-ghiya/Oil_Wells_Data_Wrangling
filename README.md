# Oil Wells Data Wrangling Project

This repository includes:
- data extraction/scraping/preprocessing outputs for Part 1
- a MySQL-backed web map for Part 2 (Apache + OpenLayers + popup details)

## 1. PDF Extraction & OCR Module

This module is responsible for systematically processing a collection of scanned PDF documents to extract well-specific information and stimulation data.

### Extraction Methodology
The script utilizes a dual-approach to ensure maximum data recovery from documents of varying quality:
- **Native Text Extraction:** Uses `pdfplumber` to extract text directly from digital PDFs.
- **OCR Fallback:** If a document is identified as a scanned image (yielding less than 200 characters of text), the script automatically converts the PDF pages to images using `pdf2image` and performs Optical Character Recognition (OCR) via `pytesseract`.

### Data Parsing
Custom processing logic and Regular Expressions (Regex) are used to identify and isolate key data fields from the raw text, including:
- **Well Identifiers:** Well File Number, Well Name, and API Number.
- **Location Details:** County, Section, Township, Range, Quarter-Quarter, and Footages.
- **Operational Data:** Operator, Spud Date, and Completion Date.
- **Stimulation Details:** Stimulation Type (e.g., Acidizing, Fracture Treatment), Field Name, and Pool.

### Output
The extracted data is structured into a tabular format and saved for further processing.
- **`extracted_wells.csv`**: Contains the raw extracted fields for all processed PDFs.

---

## 2. Web Scraping & Preprocessing Module

### Data Cleaning & Normalization
The raw PDF-extracted data contained inconsistencies, OCR noise, and formatting issues. To ensure uniformity across all records, the following steps were applied:

#### API Normalization
Raw API numbers extracted from PDFs often appear in inconsistent formats.
A normalization step converts them into the standard format: **`NN-NNN-NNNNN`**

#### Well Name Standardization
Well names extracted from PDFs may include operator prefixes, job numbers, form labels, or OCR noise.
Regex‑based rules are applied to isolate the actual well name.

#### OCR Noise Reduction
Scanned PDFs introduce random characters and artifacts.
A cleaning function removes: non‑standard characters, symbol clusters, repeated punctuation, and broken OCR fragments.

#### HTML & Whitespace Cleanup
Some fields contain HTML fragments or irregular spacing.
The preprocessing removes: HTML tags, line breaks, tabs, and excessive whitespace.


---

## 3. Web Scraping (DrillingEdge.com)

For each cleaned well entry, the module:
1. Builds a search query using the cleaned API and well name
2. Retrieves the search results page
3. Identifies the correct well detail page
4. Extracts key attributes, including: Well Status, Well Type, Closest City, Oil Produced, Gas Produced
5. Merges the scraped data back into the main dataset

A delay is added between requests to avoid rate‑limiting.

**Output:** `final_well_data.csv`

---

## 4. Final Preprocessing

After combining PDF-extracted and web-scraped data, the module performs:
- **Date Conversion:** Converts `spud_date` and `completion_date` into `YYYY-MM-DD`
- **Numeric Conversion:** Production values (e.g., "1.7 k") → numeric (e.g., 1700)
- **Missing Value Handling:** Text → "N/A", Numeric → 0
- **Coordinate Normalization:** Latitude and longitude converted to numeric where possible
  
**Output:** `final_well_data_cleaned.csv` --> used for MySQL insertion and map visualization in Part 2.

---

## 5. Initial Setup (Linux, Apache, MySQL)

1. Install Apache, PHP, and MySQL:
   - `sudo apt update`
   - `sudo apt install apache2 php libapache2-mod-php php-mysql mysql-server`
2. Start services:
   - `sudo systemctl enable --now apache2`
   - `sudo systemctl enable --now mysql`

## 6. Prepare Database

1. Create database/table:
   - `mysql -u root -p < sql/create_wells_table.sql`
2. Load cleaned data from CSV:
   - `mysql -u root -p --local-infile=1`
   - then run:

```sql
USE oil_wells;
LOAD DATA LOCAL INFILE '/absolute/path/to/final_well_data_cleaned.csv'
INTO TABLE wells
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(source_file, well_file_no, well_name, api_number, county, section, township, `range`,
 quarter_quarter, footages, @latitude, @longitude, operator, @spud_date, @completion_date,
 stimulation_type, field_name, pool, raw_text_sample, api_clean, well_name_clean, detail_url,
 well_status, well_type, closest_city, @oil_produced, @gas_produced)
SET latitude = NULLIF(@latitude, 'N/A'),
    longitude = NULLIF(@longitude, 'N/A'),
    spud_date = STR_TO_DATE(NULLIF(@spud_date, 'N/A'), '%Y-%m-%d'),
    completion_date = STR_TO_DATE(NULLIF(@completion_date, 'N/A'), '%Y-%m-%d'),
    oil_produced = NULLIF(@oil_produced, 'N/A'),
    gas_produced = NULLIF(@gas_produced, 'N/A');
```

## 7. Configure Web App

1. Copy config template:
   - `cp web/api/config.php.example web/api/config.php`
2. Edit `web/api/config.php` with your MySQL credentials and table name.
3. Place repo under Apache web root (or symlink):
   - example URL: `http://localhost/Oil_Wells_Data_Wrangling/web/`

## 8. Webpage and Mapping Requirements Implemented

- `web/index.html` provides the webpage and map display section required for Part 2.
- OpenLayers (OpenStreetMap base layer) is used to render the base map.
- The initial map view is configured in `web/app.js`.
- Well records are fetched from MySQL through `web/api/wells.php` (JSON response).
- Markers (push pins) are created from database `latitude` and `longitude` values.
- Each marker corresponds to one well location.
- Clicking a marker opens a popup overlay.
- The popup displays all returned well fields, including PDF-extracted fields and scraped well details (`well_status`, `well_type`, `closest_city`, `oil_produced`, `gas_produced`).
- If no valid coordinates are available, the page still loads and shows a status message indicating that no markers could be plotted.

## 9. Quick Validation Checklist

1. Confirm Apache is serving the copied web app from `/var/www/html/Oil_Wells_Data_Wrangling/web/`.
2. Confirm the API endpoint returns JSON: `http://localhost/Oil_Wells_Data_Wrangling/web/api/wells.php`
3. Open the map page: `http://localhost/Oil_Wells_Data_Wrangling/web/`
4. Confirm the base map tiles load and the page status message updates after data fetch.
5. If the database contains valid coordinates, confirm markers are displayed and clicking a marker opens a popup with complete well details.
6. If no markers are shown, verify: `SELECT COUNT(*) FROM wells WHERE latitude IS NOT NULL AND longitude IS NOT NULL;`
7. Note: `final_well_data_cleaned.csv` loads successfully, but contains no valid latitude/longitude values, so the expected marker count is `0`.

## 10. Scripts

- **Part 1 / data processing:**
  - `Oil_Well_OCR.ipynb` (PDF extraction / OCR workflow)
  - `scraper.py` (DrillingEdge scraping and merge into `final_well_data.csv`)
  - `preprocess.py` (cleanup, normalization, type conversion into `final_well_data_cleaned.csv`)
- **Part 2 / web access and visualization:**
  - `sql/create_wells_table.sql` (MySQL schema)
  - `web/index.html`, `web/styles.css`, `web/app.js`
  - `web/api/config.php.example`, `web/api/wells.php`
- **Data outputs:** `extracted_wells.csv`, `final_well_data.csv`, `final_well_data_cleaned.csv`

## 11. How to Run

```
python scraper.py
python preprocess.py
```

## 12. Dependencies

```bash
pip install -r requirements.txt
```
