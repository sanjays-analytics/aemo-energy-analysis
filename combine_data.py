"""
Consolidates AEMO's monthly price and demand CSVs into a single
cleaned dataset, ready for loading into MySQL.

Run this after download_aemo_data.py has populated the aemo_data
folder with all region/month CSV files.
"""

from pathlib import Path
import pandas as pd

# %%
# ------------------------------------------------------------
# Step 1: find every downloaded CSV, regardless of subfolder
# depth (organised by state, then year).
# ------------------------------------------------------------
csv_files = list(Path("aemo_data").rglob("*.csv"))
print(f"Found {len(csv_files)} files")  # expect 220


# %%
# ------------------------------------------------------------
# Step 2: read every file into its own small dataframe, collect
# them in a list, and concatenate once at the end. Concatenating
# inside the loop instead would rebuild a growing dataframe from
# scratch on every iteration, dramatically slower as it grows.
# ------------------------------------------------------------
dataframes = []
for file in csv_files:
    df = pd.read_csv(file)
    dataframes.append(df)

combined = pd.concat(dataframes, ignore_index=True)
print(combined.shape)  # expect (1928160, 5)
print(combined.head())


# %%
# ------------------------------------------------------------
# Step 3: data quality checks, before trusting the data enough
# to build anything on top of it.
# ------------------------------------------------------------
print(combined['SETTLEMENTDATE'].apply(type).value_counts())  # confirm all strings, no mixed types
print(combined['PERIODTYPE'].value_counts())  # confirm whether this column ever varies
print(combined.isnull().sum())  # confirm no missing values anywhere


# %%
# ------------------------------------------------------------
# Step 4: convert SETTLEMENTDATE to a real datetime type, now
# that the format's confirmed consistent across all 220 files.
# Drop PERIODTYPE, confirmed constant (always 'TRADE'), so it
# carries no information and isn't earning its place.
# ------------------------------------------------------------
combined['SETTLEMENTDATE'] = pd.to_datetime(combined['SETTLEMENTDATE'])
combined = combined.drop(columns=['PERIODTYPE'])


# %%
# ------------------------------------------------------------
# Step 5: build the calendar attributes directly from the
# datetime column, using Australian season boundaries, not the
# Northern Hemisphere default most libraries assume.
# ------------------------------------------------------------
combined['day_of_week'] = combined['SETTLEMENTDATE'].dt.day_name()
combined['is_weekend'] = combined['SETTLEMENTDATE'].dt.dayofweek >= 5
combined['month'] = combined['SETTLEMENTDATE'].dt.month
combined['quarter'] = combined['SETTLEMENTDATE'].dt.quarter

season_map = {
    1: 'Summer', 2: 'Summer', 12: 'Summer',
    3: 'Autumn', 4: 'Autumn', 5: 'Autumn',
    6: 'Winter', 7: 'Winter', 8: 'Winter',
    9: 'Spring', 10: 'Spring', 11: 'Spring',
}
combined['season'] = combined['month'].map(season_map)

# Sanity check: every month should show a real season, not NaN
print(combined[['month', 'season']].drop_duplicates().sort_values('month'))


# %%
# ------------------------------------------------------------
# Step 6: build the date-only column needed to join readings to
# a calendar dimension, then build that dimension as one row
# per unique date rather than repeating calendar attributes on
# every one of the 1.9M individual readings.
#
# Known edge case: this produces 1,340 dates, one more than the
# true 1,339-day range. AEMO timestamps each settlement period
# by when it ends, so the very last 5-minute period of August
# 31st carries a 2026-09-01 00:00:00 timestamp, one boundary
# reading per region. Left as-is rather than reassigned, since
# it affects only 5 rows total and is documented instead.
# ------------------------------------------------------------
combined['reading_date'] = combined['SETTLEMENTDATE'].dt.date

calendar_dim = combined[
    ['reading_date', 'day_of_week', 'is_weekend', 'month', 'quarter', 'season']
].drop_duplicates()
print(calendar_dim.shape)  # expect (1340, 6)


# %%
# ------------------------------------------------------------
# Step 7: split into the fact table (readings) and dimension
# table (regions), replacing the region code with a proper
# surrogate integer key for the SQL schema.
# ------------------------------------------------------------
readings = combined[['REGION', 'SETTLEMENTDATE', 'reading_date', 'TOTALDEMAND', 'RRP']].copy()

regions = combined[['REGION']].drop_duplicates().reset_index(drop=True)
regions.insert(0, 'region_id', regions.index + 1)
print(regions)

region_map = dict(zip(regions['REGION'], regions['region_id']))
readings['region_id'] = readings['REGION'].map(region_map)
readings = readings.drop(columns=['REGION'])
print(readings.head())


# %%
# ------------------------------------------------------------
# Step 8: export all three cleaned tables to CSV, so a VS Code
# kernel restart never means re-running the full 220-file
# consolidation again.
# ------------------------------------------------------------
combined.to_csv('aemo_combined_clean.csv', index=False)
regions.to_csv('regions_clean.csv', index=False)
calendar_dim.to_csv('calendar_dim_clean.csv', index=False)
print("Exported all three cleaned CSVs.")
