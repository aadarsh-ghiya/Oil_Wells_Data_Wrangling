import re
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup

# 1) CLEANING FUNCTIONS

def normalize_api(api_raw: str) -> str | None:
    if pd.isna(api_raw):
        return None
    api_raw = str(api_raw)
    digits = re.sub(r"\D", "", api_raw)
    if len(digits) != 10:
        return None
    return f"{digits[0:2]}-{digits[2:5]}-{digits[5:]}"


def clean_well_name(name_raw):
    if pd.isna(name_raw):
        return None

    name = str(name_raw).strip()

    operator_prefixes = [
        "Oasis Petroleum North America LLC", "Oasis Petroleum",
        "Continental Resources Inc.", "Continental Resources",
        "Continental", "SM Energy", "RIM Operating",
        "Slawson Exploration Company, Inc.", "Slawson Exploration",
        "Versatile Energy", "Hill Electric, Inc",
        "NANCE PETROLEUM CORPORATION", "Oasis", "SM"
    ]

    for op in operator_prefixes:
        if name.lower().startswith(op.lower()):
            name = name[len(op):].strip()

    prefixes = [
        "Spacing Unit Description", "Job #", "Otr-Otr", "Horizontal Well",
        "HORIZONTAL WELL", "Well Evaluation", "County swsw", "County",
        "Range County", "Range", "Address", "Permit", "Name"
    ]

    for p in prefixes:
        if name.lower().startswith(p.lower()):
            name = name[len(p):].strip()

    name = name.replace("#", "").strip()

    # 1) Standard wells: WORD WORD 5300 41-18H
    pattern1 = r"[A-Za-z][A-Za-z &]*\s+\d{4}\s+\d{1,2}-\d{1,2}[A-Za-z]*"
    m1 = re.search(pattern1, name)
    if m1:
        return m1.group(0).strip()

    # 2) Wells without 4-digit block: MAGNUM 2-36
    pattern2 = r"[A-Za-z][A-Za-z &]*\s+\d{1,2}-\d{1,2}[A-Za-z]*"
    m2 = re.search(pattern2, name)
    if m2:
        return m2.group(0).strip()

    # 3) SWD wells
    pattern3 = r"[A-Za-z][A-Za-z &]*SWD\s+\d{4}\s+\d{1,2}-\d{1,2}"
    m3 = re.search(pattern3, name)
    if m3:
        return m3.group(0).strip()

    # 4) Multi-section wells: 44-2412T
    pattern4 = r"[A-Za-z][A-Za-z &]*\s+\d{4}\s+\d{2}-\d{2}\d{2}[A-Za-z]*"
    m4 = re.search(pattern4, name)
    if m4:
        return m4.group(0).strip()

    # 5) Job numbers → mark as None
    if re.match(r"^(S|ND)\d+", name):
        return None

    return name


# 2) SEARCH DRILLINGEDGE

BASE = "https://www.drillingedge.com/search"

def search_drillingedge(api_no, well_name):
    params = {
        "type": "wells",
        "operator_name": "",
        "well_name": well_name,
        "api_no": api_no,
        "lease_key": "",
        "state": "",
        "county": "",
        "section": "",
        "township": "",
        "range": "",
        "min_boe": "",
        "max_boe": "",
        "min_depth": "",
        "max_depth": "",
        "field_formation": ""
    }

    r = requests.get(BASE, params=params, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    return BeautifulSoup(r.text, "html.parser")


def extract_detail_link(soup, api_no):
    rows = soup.select("table tr")
    if not rows:
        return None

    for row in rows:
        cols = [c.get_text(strip=True) for c in row.find_all("td")]
        if api_no in cols:
            a = row.find("a")
            if a and a.get("href"):
                href = a["href"]
                if href.startswith("http"):
                    return href
                return "https://www.drillingedge.com" + href

    for row in rows:
        a = row.find("a")
        if a and a.get("href"):
            href = a["href"]
            if href.startswith("http"):
                return href
            return "https://www.drillingedge.com" + href

    return None

# 3) SCRAPE WELL DETAILS

def extract_well_details(url):
    if not isinstance(url, str) or not url.startswith("http"):
        return None

    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=40)
    if r.status_code != 200:
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    details = {
        "well_status": "N/A",
        "well_type": "N/A",
        "closest_city": "N/A",
        "oil_produced": "N/A",
        "gas_produced": "N/A"
    }

    skinny = soup.select_one("table.skinny")
    if skinny:
        rows = skinny.find_all("tr")
        for row in rows:
            cells = row.find_all(["th", "td"])
            for i in range(0, len(cells) - 1, 2):
                key = cells[i].get_text(strip=True)
                val = cells[i+1].get_text(strip=True)

                if key == "Well Status":
                    details["well_status"] = val
                elif key == "Well Type":
                    details["well_type"] = val
                elif key == "Closest City":
                    details["closest_city"] = val

    drops = soup.select("span.dropcap")
    if len(drops) >= 1:
        details["oil_produced"] = drops[0].get_text(strip=True)
    if len(drops) >= 2:
        details["gas_produced"] = drops[1].get_text(strip=True)

    return details


# 4) MAIN PIPELINE

def main():
    df = pd.read_csv("extracted_wells.csv")

    df["api_clean"] = df["api_number"].apply(normalize_api)
    df["well_name_clean"] = df["well_name"].apply(clean_well_name)
    df["detail_url"] = None

    output = []

    for idx, row in df.iterrows():
        print(f"Processing {idx+1}/{len(df)}: {row['well_name_clean']}")

        api_no = row["api_clean"]
        well = row["well_name_clean"]

        if pd.isna(api_no):
            print("Skipped (invalid API)")
            continue

        soup = search_drillingedge(api_no, well)
        link = extract_detail_link(soup, api_no)
        df.at[idx, "detail_url"] = link

        details = extract_well_details(link) if link else None
        if details is None:
            details = {
                "well_status": "N/A",
                "well_type": "N/A",
                "closest_city": "N/A",
                "oil_produced": "N/A",
                "gas_produced": "N/A"
            }

        output.append({**row.to_dict(), **details})
        time.sleep(1)

    pd.DataFrame(output).to_csv("final_well_data.csv", index=False)
    print("Saved final_well_data.csv")


if __name__ == "__main__":
    main()