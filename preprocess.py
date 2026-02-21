import pandas as pd
import numpy as np
import re
from bs4 import BeautifulSoup

# 1) CLEANING HELPERS

def remove_html(text):
    """Strip HTML tags from text."""
    if pd.isna(text):
        return None
    return BeautifulSoup(str(text), "lxml").get_text(" ", strip=True)


def clean_text(text):
    """Remove special characters, normalize whitespace."""
    if pd.isna(text):
        return None
    text = str(text)
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def to_date(value):
    """Convert to datetime, return NaT if invalid."""
    return pd.to_datetime(value, errors="coerce")


def to_numeric(value):
    """Convert oil/gas production values like '1.7 k' → 1700."""
    if pd.isna(value):
        return 0

    value = str(value).strip().lower()

    if value in ["n/a", "na", "", "none"]:
        return 0

    # Handle "1.7 k" → 1700
    if "k" in value:
        try:
            return float(value.replace("k", "").strip()) * 1000
        except:
            return 0

    # Handle plain numbers
    try:
        return float(value)
    except:
        return 0

def remove_ocr_unwanted(text):
    if pd.isna(text):
        return None
    text = str(text)

    # Remove sequences of weird symbols
    text = re.sub(r"[_\-–—•·•…:;=~`^]+", " ", text)

    # Remove any non-standard characters
    text = re.sub(r"[^0-9A-Za-z.,;:()&/%$#@!?\s'-]", " ", text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()

# 2) MAIN PREPROCESSING PIPELINE

def preprocess():
    df = pd.read_csv("final_well_data.csv")

    # Clean text fields (INCLUDING raw_text_sample)
    text_columns = [
        "well_name",
        "well_name_clean",
        "operator",
        "field_name",
        "pool",
        "raw_text_sample",
        "well_status",
        "well_type",
        "closest_city"
    ]

    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].apply(remove_html).apply(clean_text).apply(remove_ocr_unwanted)

    # Convert dates
    if "spud_date" in df.columns:
        df["spud_date"] = df["spud_date"].apply(to_date)

    if "completion_date" in df.columns:
        df["completion_date"] = df["completion_date"].apply(to_date)

    # Convert oil/gas production to numeric
    if "oil_produced" in df.columns:
        df["oil_produced"] = df["oil_produced"].apply(to_numeric)

    if "gas_produced" in df.columns:
        df["gas_produced"] = df["gas_produced"].apply(to_numeric)

    # Ensure latitude/longitude are numeric
    if "latitude" in df.columns:
        df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")

    if "longitude" in df.columns:
        df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    # Replace missing values
    df = df.fillna("N/A")

    # Save cleaned output
    df.to_csv("final_well_data_cleaned.csv", index=False)
    print("Saved → final_well_data_cleaned.csv")


if __name__ == "__main__":
    preprocess()