-- Databricks Free Edition exercise on the NASA PCoE battery dataset
-- Table: workspace.default.nasa_battery_capacity_vs_cycle
-- Columns: cell_id, cycle, capacity_ah, ambient_temp_c (4 cells, 636 rows)

-- 01_cycle_summary: cycles and capacity range per cell
SELECT
  cell_id,
  COUNT(*)                  AS cycles,
  ROUND(MAX(capacity_ah),4) AS max_capacity,
  ROUND(MIN(capacity_ah),4) AS min_capacity,
  ROUND(AVG(capacity_ah),4) AS avg_capacity
FROM workspace.default.nasa_battery_capacity_vs_cycle
GROUP BY cell_id
ORDER BY cell_id;

-- 02_capacity_fade: capacity retention vs the first cycle (window function)
SELECT
  cell_id,
  cycle,
  ROUND(capacity_ah, 4) AS capacity_ah,
  ROUND(FIRST_VALUE(capacity_ah) OVER (PARTITION BY cell_id ORDER BY cycle), 4) AS initial_capacity_ah,
  ROUND(100 * capacity_ah
        / FIRST_VALUE(capacity_ah) OVER (PARTITION BY cell_id ORDER BY cycle), 1) AS retention_pct
FROM workspace.default.nasa_battery_capacity_vs_cycle
WHERE cycle = 1 OR cycle % 20 = 0
ORDER BY cell_id, cycle;

-- 03_data_quality: nulls, duplicates, gaps and out-of-range values per cell
SELECT
  cell_id,
  COUNT(*)                                                    AS row_count,
  SUM(CASE WHEN capacity_ah IS NULL THEN 1 ELSE 0 END)        AS null_capacity,
  COUNT(*) - COUNT(DISTINCT cycle)                            AS duplicate_cycles,
  MAX(cycle) - MIN(cycle) + 1 - COUNT(DISTINCT cycle)         AS missing_cycles,
  SUM(CASE WHEN capacity_ah <= 0 OR capacity_ah > 2.5
           THEN 1 ELSE 0 END)                                 AS out_of_range
FROM workspace.default.nasa_battery_capacity_vs_cycle
GROUP BY cell_id
ORDER BY cell_id;
