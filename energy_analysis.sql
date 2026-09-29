CREATE DATABASE IF NOT EXISTS energy_market;
USE energy_market;

CREATE TABLE regions (
  region_id INT NOT NULL,
  region_code VARCHAR(10) NOT NULL,
  PRIMARY KEY (region_id),
  UNIQUE KEY uq_region_code (region_code)
);

CREATE TABLE calendar_dim (
  reading_date DATE NOT NULL,
  day_of_week VARCHAR(10),
  is_weekend TINYINT,
  month INT,
  quarter INT,
  season VARCHAR(10),
  PRIMARY KEY (reading_date)
);

CREATE TABLE readings (
  reading_id INT NOT NULL AUTO_INCREMENT,
  region_id INT NOT NULL,
  settlement_datetime DATETIME NOT NULL,
  reading_date DATE NOT NULL, reading_date
  total_demand DECIMAL(10,2),
  rrp DECIMAL(10,2),
  PRIMARY KEY (reading_id),
  FOREIGN KEY (region_id) REFERENCES regions(region_id),
  FOREIGN KEY (reading_date) REFERENCES calendar_dim(reading_date)
);

#-----------------------------------------------------------------------#

USE energy_market;
SELECT COUNT(*) FROM regions;
SELECT COUNT(*) FROM calendar_dim;
SELECT COUNT(*) FROM readings;

#-----------------------------------------------------------------------#

SELECT AVG(r.rrp) AS average_price,
       AVG(r.total_demand) AS average_demand,
       reg.region_code
FROM readings r
JOIN regions reg ON r.region_id = reg.region_id
GROUP BY reg.region_code;

#-----------------------------------------------------------------------#

SELECT reg.region_code,
       COUNT(*) AS negative_price_events,
       MIN(r.rrp) AS most_negative_price
FROM readings r
JOIN regions reg ON r.region_id = reg.region_id
WHERE r.rrp < 0
GROUP BY reg.region_code
ORDER BY negative_price_events DESC;

#-----------------------------------------------------------------------#

SELECT YEAR(c.reading_date) AS year,
       c.month,
       ROUND(STDDEV(r.rrp), 2) AS price_volatility
FROM readings r
JOIN calendar_dim c ON r.reading_date = c.reading_date
WHERE NOT (YEAR(c.reading_date) = 2026 AND c.month = 9)
GROUP BY YEAR(c.reading_date), c.month
ORDER BY year, c.month;

-- SELECT YEAR(c.reading_date) AS year, c.month, COUNT(*) AS reading_count
-- FROM readings r
-- JOIN calendar_dim c ON r.reading_date = c.reading_date
-- WHERE YEAR(c.reading_date) = 2026 AND c.month = 9
-- GROUP BY YEAR(c.reading_date), c.month;
#-----------------------------------------------------------------------#

SELECT reg.region_code,
       (AVG(r.total_demand * r.rrp) - AVG(r.total_demand) * AVG(r.rrp))
       / (STDDEV(r.total_demand) * STDDEV(r.rrp)) AS correlation
FROM readings r
JOIN regions reg ON r.region_id = reg.region_id
GROUP BY reg.region_code;
