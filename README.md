# AEMO Energy Market Analysis

An analysis of Australia's National Electricity Market (NEM) wholesale price and demand data across all 5 regions, from January 2023 through August 2026. Part of a wider project mixing Python, SQL, Excel, and Power BI, moving from raw data acquisition through to a retail pricing model.

**Status: in progress. Data pipeline and core SQL queries complete. Python deep-dive, Excel margin model, and Power BI dashboard to follow.**

## Data source

AEMO's [Aggregated Price and Demand Data](https://aemo.com.au/energy-systems/electricity/national-electricity-market-nem/data-nem/aggregated-data), published as monthly CSV files per region. Covers NSW1, QLD1, SA1, TAS1, and VIC1, at 5-minute settlement intervals (the format AEMO has used since October 2021, chosen specifically to avoid mixing granularities with the older 30-minute format).

## Data pipeline

- `download_aemo_data.py`: bulk-downloads all monthly files across all 5 regions for the chosen date range directly from AEMO's public URLs, 220 files in total.
- Python (pandas): consolidates all 220 files into one dataset, verifies consistent columns and formats across every file, confirms zero missing values, and builds a calendar dimension (day of week, weekend flag, month, quarter, and Australian season) from the timestamp.
- `PERIODTYPE` was dropped after confirming it never varies across all 1.9 million rows, always `TRADE`.
- Given the dataset's size (1,928,160 rows), data is loaded directly from Python into MySQL via SQLAlchemy rather than MySQL Workbench's Import Wizard.

## Schema

A genuine star schema, the first true fact-and-dimensions design in this portfolio:

- **regions**: 5 rows, one per NEM region.
- **calendar_dim**: 1,340 rows, one per calendar date, holding day of week, weekend flag, month, quarter, and season.
- **readings** (fact table): 1,928,160 rows, one per region per 5-minute settlement period, holding demand and price, foreign keyed to both `regions` and `calendar_dim`.

Known edge case: a small number of boundary readings (5 rows, one per region) are timestamped into 2026-09-01, since AEMO labels each settlement period by its end time rather than its start. This affects one calendar date only and is excluded from any month-level analysis rather than treated as a real month.

## Files

- `download_aemo_data.py`: the bulk data acquisition script.
- `schema_and_load.sql` / load script: creates the three tables and loads them from the cleaned Python output.
- `core_queries.sql`: the four core analytical queries, each preceded by the question it answers.

## Findings so far

- **Average price and demand by region**: NSW1 has both the highest average price ($103.81) and highest average demand (7,535 MW), consistent with it being the largest NEM region. VIC1 has the lowest average price ($68.31) despite the second-highest demand (4,848 MW), likely reflecting its historically heavy reliance on low-cost brown coal baseload generation.
- **Price volatility by month**: varies substantially, from as low as $19 in an excluded partial month to a peak of $994.82 in June 2025, roughly double the next-highest month. Winter months generally trend more volatile, consistent with heating demand spikes and lower solar output, though June 2025 specifically stands out enough to be worth investigating against real grid events.
- **Negative price events**: all four mainland regions bottom out at exactly -$1,000.00, AEMO's regulatory Market Price Floor. SA1 recorded negative prices in 26% of all its settlement periods, the highest by far, consistent with South Australia's very high rooftop solar and wind penetration relative to grid size. TAS1, predominantly hydro-powered, saw negative prices in under 5% of periods and never touched the exact price floor.
- **Demand-price correlation**: positive in every region, as expected, but weak everywhere (0.12 to 0.23), confirming that price is driven by far more than demand alone. VIC1 shows the strongest relationship (0.235), TAS1 the weakest (0.120), plausibly reflecting Tasmania's hydro generation responding to water availability as much as real-time demand.

## Next steps

Python: deeper time-series volatility analysis, seasonal demand patterns, and investigation of the June 2025 volatility spike.

Excel: a retail pricing/margin calculator, translating wholesale price behaviour into what a retailer would need to charge.

Power BI: a regional market dashboard covering price and demand trends, volatility, and negative price events.
