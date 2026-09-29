-- ============================================================
-- AEMO Energy Market Analysis
-- Schema creation
-- ============================================================
-- Creates the star schema: regions and calendar_dim (dimensions)
-- and readings (fact table). The actual data load does not
-- happen here, given the dataset's size (1.9M+ rows), the
-- cleaned data is loaded directly from Python via SQLAlchemy
-- instead (see load_to_mysql.py), not through this script or
-- the MySQL Workbench Import Wizard.
-- ============================================================

CREATE DATABASE IF NOT EXISTS energy_market;
USE energy_market;


-- Dimension: one row per NEM region.
CREATE TABLE regions (
    region_id   INT AUTO_INCREMENT PRIMARY KEY,
    region_code VARCHAR(10) NOT NULL UNIQUE
);


-- Dimension: one row per calendar date across the dataset's
-- date range, holding the calendar attributes built in
-- combine_data.py (day of week, weekend flag, month, quarter,
-- Australian season).
CREATE TABLE calendar_dim (
    reading_date DATE PRIMARY KEY,
    day_of_week  VARCHAR(10) NOT NULL,
    is_weekend   TINYINT(1) NOT NULL,
    month        INT NOT NULL,
    quarter      INT NOT NULL,
    season       VARCHAR(10) NOT NULL
);


-- Fact table: one row per region per 5-minute settlement
-- period. reading_date is a foreign key into calendar_dim
-- rather than deriving the date again at query time.
CREATE TABLE readings (
    reading_id           INT AUTO_INCREMENT PRIMARY KEY,
    settlement_datetime  DATETIME NOT NULL,
    region_id            INT NOT NULL,
    reading_date         DATE NOT NULL,
    total_demand         DECIMAL(10, 2) NOT NULL,
    rrp                  DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (region_id) REFERENCES regions(region_id),
    FOREIGN KEY (reading_date) REFERENCES calendar_dim(reading_date)
);
