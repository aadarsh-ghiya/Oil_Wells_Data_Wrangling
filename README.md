# Web Scraping & Preprocessing Module

## Overview
This module handles the cleaning, normalization, web scraping, and preprocessing of oil‑well data extracted from scanned PDF files.  
The goal is to transform raw PDF text and external web‑scraped information into a structured dataset suitable for database storage and map visualization in Part 2 of the project.

---

## 1. Data Cleaning & Normalization

### API Normalization
Raw API numbers extracted from PDFs often appear in inconsistent formats.  
A normalization step converts them into the standard format:

**`NN-NNN-NNNNN`**

### Well Name Standardization
Well names extracted from PDFs may include operator prefixes, job numbers, form labels, or OCR noise.  
Regex‑based rules are applied to isolate the actual well name.

### OCR Noise Reduction
Scanned PDFs introduce random characters and artifacts.  
A cleaning function removes:

- non‑standard characters  
- symbol clusters  
- repeated punctuation  
- broken OCR fragments  

This ensures the text is readable and database‑safe.

### HTML & Whitespace Cleanup
Some fields contain HTML fragments or irregular spacing.  
The preprocessing removes:

- HTML tags  
- line breaks  
- tabs  
- excessive whitespace  

---

## 2. Web Scraping (DrillingEdge.com)

For each cleaned well entry, the module:

1. Builds a search query using the cleaned API and well name  
2. Retrieves the search results page  
3. Identifies the correct well detail page  
4. Extracts key attributes, including:  
   - Well Status  
   - Well Type  
   - Closest City  
   - Oil Produced  
   - Gas Produced  
5. Merges the scraped data back into the main dataset  

A delay is added between requests to avoid rate‑limiting.

---

## 3. Final Preprocessing

After combining PDF‑extracted and web‑scraped data, the module performs:

### Date Conversion
Converts `spud_date` and `completion_date` into a consistent, database‑friendly format (`YYYY‑MM‑DD`).

### Numeric Conversion
Production values such as `"1.7 k"` or `"5.3 k"` are converted into numeric values (e.g., `1700`, `5300`).

### Missing Value Handling
- Text fields → `"N/A"`  
- Numeric fields → `0`  

### Coordinate Normalization
Latitude and longitude fields are converted to numeric types where possible.

### Output
The final cleaned dataset is saved as:
final_well_data_cleaned.csv


This file is used for MySQL insertion and map visualization in Part 2.

---

## 4. Files in This Module

| File | Description |
|------|-------------|
| `combined_scraper.py` | Cleans API & well names, scrapes DrillingEdge, merges results |
| `preprocessing.py` | Cleans text, removes OCR noise, converts dates & numbers |
| `final_well_data_cleaned.csv` | Final cleaned dataset used for database + mapping |

---

## 5. How to Run
`python combined_scraper.py python preprocessing.py`

## 6. Dependencies
Install required packages using:
`pip install -r requirements.txt`
