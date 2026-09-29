"""
Downloads AEMO's Aggregated Price and Demand Data for all 5 NEM regions,
across a chosen date range, as monthly CSV files.

URL pattern confirmed from the live AEMO download page:
https://www.aemo.com.au/aemo/data/nem/priceanddemand/PRICE_AND_DEMAND_{YYYYMM}_{REGION}.csv
"""

import os
import time
from datetime import date
import requests

# ---- Settings you can change ----
START_YEAR_MONTH = (2023, 1)   # (year, month) to start from
REGIONS = ["NSW1", "QLD1", "SA1", "TAS1", "VIC1"]
OUTPUT_DIR = "aemo_data"
DELAY_SECONDS = 1              # polite delay between requests
# ----------------------------------

BASE_URL = "https://www.aemo.com.au/aemo/data/nem/priceanddemand/PRICE_AND_DEMAND_{ym}_{region}.csv"


def month_range(start_year, start_month):
    """Yield (year, month) tuples from the start date up to last complete month."""
    today = date.today()
    # Last complete month = previous calendar month
    if today.month == 1:
        end_year, end_month = today.year - 1, 12
    else:
        end_year, end_month = today.year, today.month - 1

    year, month = start_year, start_month
    while (year, month) <= (end_year, end_month):
        yield year, month
        month += 1
        if month > 12:
            month = 1
            year += 1


def download_one(year, month, region):
    ym = f"{year}{month:02d}"
    url = BASE_URL.format(ym=ym, region=region)
    filename = f"PRICE_AND_DEMAND_{ym}_{region}.csv"
    out_path = os.path.join(OUTPUT_DIR, filename)

    if os.path.exists(out_path):
        print(f"  already have {filename}, skipping")
        return True

    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    if response.status_code == 200:
        with open(out_path, "wb") as f:
            f.write(response.content)
        print(f"  downloaded {filename}")
        return True
    else:
        print(f"  MISSING or failed ({response.status_code}): {filename}")
        return False


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    months = list(month_range(*START_YEAR_MONTH))
    total = len(months) * len(REGIONS)
    print(f"Planning to fetch {total} files: {len(months)} months x {len(REGIONS)} regions")

    done = 0
    failed = []
    for year, month in months:
        for region in REGIONS:
            ok = download_one(year, month, region)
            done += 1
            if not ok:
                failed.append((year, month, region))
            time.sleep(DELAY_SECONDS)

    print(f"\nFinished. {done - len(failed)}/{total} succeeded.")
    if failed:
        print("Failed or missing:")
        for year, month, region in failed:
            print(f"  {year}-{month:02d} {region}")


if __name__ == "__main__":
    main()
