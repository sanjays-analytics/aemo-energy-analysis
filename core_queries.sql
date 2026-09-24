-- ============================================================
-- AEMO Energy Market Analysis
-- Core SQL queries
-- ============================================================
-- Run schema_and_load.sql first (creates regions, calendar_dim,
-- readings and loads them via Python/SQLAlchemy, not the
-- Import Wizard, given the dataset's size).
-- ============================================================

USE energy_market;


-- Q1. Average wholesale price and average demand, per region,
-- across the full dataset (Jan 2023 to Aug 2026).
SELECT AVG(r.rrp) AS average_price,
       AVG(r.total_demand) AS average_demand,
       reg.region_code
FROM readings r
JOIN regions reg ON r.region_id = reg.region_id
GROUP BY reg.region_code;


-- Q2. Price volatility by month, measured as the standard
-- deviation of price within each calendar month.
-- September 2026 is excluded: it contains only 5 rows, the
-- boundary readings from August 31st that inherited a
-- September timestamp (AEMO labels each period by its end
-- time), not a genuine month of data.
SELECT YEAR(c.reading_date) AS year,
       c.month,
       ROUND(STDDEV(r.rrp), 2) AS price_volatility
FROM readings r
JOIN calendar_dim c ON r.reading_date = c.reading_date
WHERE NOT (YEAR(c.reading_date) = 2026 AND c.month = 9)
GROUP BY YEAR(c.reading_date), c.month
ORDER BY year, c.month;


-- Q3. How many negative price events occurred per region, and
-- what was the most extreme one?
-- A negative price means generators are effectively paying
-- the grid to keep running, usually caused by renewable
-- oversupply outstripping demand.
SELECT reg.region_code,
       COUNT(*) AS negative_price_events,
       MIN(r.rrp) AS most_negative_price
FROM readings r
JOIN regions reg ON r.region_id = reg.region_id
WHERE r.rrp < 0
GROUP BY reg.region_code
ORDER BY negative_price_events DESC;


-- Q4. Correlation between demand and price, per region.
-- MySQL has no built-in CORR() function, so this is built
-- directly from the standard formula: covariance divided by
-- the product of both variables' standard deviations.
SELECT reg.region_code,
       (AVG(r.total_demand * r.rrp) - AVG(r.total_demand) * AVG(r.rrp))
       / (STDDEV(r.total_demand) * STDDEV(r.rrp)) AS correlation
FROM readings r
JOIN regions reg ON r.region_id = reg.region_id
GROUP BY reg.region_code;
