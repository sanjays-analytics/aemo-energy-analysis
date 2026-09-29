"""
Loads the cleaned AEMO data (regions, calendar_dim, readings) directly
into MySQL using SQLAlchemy, bypassing the Import Wizard since this
dataset is far too large (1.9M+ rows) for that to be practical.

Run this after combine_data.py has produced: regions, calendar_dim,
readings dataframes in memory (or adapt to read from saved CSVs).
"""

from sqlalchemy import create_engine

# ---- Update these to match your MySQL setup ----
DB_USER = "root"
DB_PASSWORD = "********"
DB_HOST = "localhost"
DB_NAME = "energy_market"
# --------------------------------------------------

engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")

# ---- Rename columns to match the SQL schema exactly ----
regions_load = regions.rename(columns={"REGION": "region_code"})

calendar_load = calendar_dim.copy()  # columns already match

readings_load = readings.rename(columns={
    "SETTLEMENTDATE": "settlement_datetime",
    "TOTALDEMAND": "total_demand",
    "RRP": "rrp",
})

# ---- Load smallest tables first (order matters: FK dependencies) ----
print("Loading regions...")
regions_load.to_sql("regions", engine, if_exists="append", index=False)

print("Loading calendar_dim...")
calendar_load.to_sql("calendar_dim", engine, if_exists="append", index=False)

print("Loading readings (1.9M+ rows, this will take a few minutes)...")
readings_load.to_sql(
    "readings",
    engine,
    if_exists="append",
    index=False,
    chunksize=10000,   # insert in batches, not all 1.9M at once
    method="multi",    # batches multiple rows per INSERT statement
)

print("Done.")
