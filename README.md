# Oil Wells Data Wrangling

This repository includes:
- data extraction/scraping/preprocessing outputs for Part 1
- a MySQL-backed web map for Part 2 (Apache + OpenLayers + popup details)

## 1) Initial Setup (Linux, Apache, MySQL)

1. Install Apache, PHP, and MySQL:
   - `sudo apt update`
   - `sudo apt install apache2 php libapache2-mod-php php-mysql mysql-server`
2. Start services:
   - `sudo systemctl enable --now apache2`
   - `sudo systemctl enable --now mysql`

## 2) Prepare Database

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

## 3) Configure Web App

1. Copy config template:
   - `cp web/api/config.php.example web/api/config.php`
2. Edit `web/api/config.php` with your MySQL credentials and table name.
3. Place repo under Apache web root (or symlink):
   - example URL: `http://localhost/Oil_Wells_Data_Wrangling/web/`

## 4) Webpage and Mapping Requirements Implemented

- `web/index.html` provides the webpage and map display section required for Part 2.
- OpenLayers (OpenStreetMap base layer) is used to render the base map.
- The initial map view is configured in `web/app.js`.
- Well records are fetched from MySQL through `web/api/wells.php` (JSON response).
- Markers (push pins) are created from database `latitude` and `longitude` values.
- Each marker corresponds to one well location.
- Clicking a marker opens a popup overlay.
- The popup displays all returned well fields, including PDF-extracted fields and scraped well details (`well_status`, `well_type`, `closest_city`, `oil_produced`, `gas_produced`).
- If no valid coordinates are available, the page still loads and shows a status message indicating that no markers could be plotted.

## 5) Quick Validation Checklist

1. Confirm Apache is serving the copied web app from `/var/www/html/Oil_Wells_Data_Wrangling/web/`.
2. Confirm the API endpoint returns JSON:
   - `http://localhost/Oil_Wells_Data_Wrangling/web/api/wells.php`
3. Open the map page in a browser:
   - `http://localhost/Oil_Wells_Data_Wrangling/web/`
4. Confirm the base map tiles load and the page status message updates after data fetch.
5. If the database contains valid coordinates, confirm markers are displayed and clicking a marker opens a popup with complete well details.
6. If no markers are shown, verify coordinate availability in MySQL:
   - `SELECT COUNT(*) FROM wells WHERE latitude IS NOT NULL AND longitude IS NOT NULL;`
7. Note for the current provided dataset: `final_well_data_cleaned.csv` loads successfully, but it contains no valid latitude/longitude values, so the expected marker count is `0`.

## Scripts

- Part 1 / data processing:
  - `Oil_Well_OCR.ipynb` (PDF extraction / OCR workflow)
  - `scraper.py` (DrillingEdge scraping and merge into `final_well_data.csv`)
  - `preprocess.py` (cleanup, normalization, type conversion into `final_well_data_cleaned.csv`)
- Part 2 / web access and visualization:
  - `sql/create_wells_table.sql` (MySQL schema)
  - `web/index.html` (webpage + map container)
  - `web/styles.css` (map/popup styling)
  - `web/app.js` (OpenLayers map, markers, popup logic)
  - `web/api/config.php.example` (API DB config template)
  - `web/api/wells.php` (PHP API endpoint to query MySQL)
- Data outputs:
  - `extracted_wells.csv`
  - `final_well_data.csv`
  - `final_well_data_cleaned.csv`
