# Cloud exercises: NASA battery data in Databricks

A small side exercise on the same NASA PCoE battery dataset used by the Battery Digital Twin.
The goal was to practise SQL, window functions, data quality checks and a PySpark notebook on a managed cloud platform (Databricks Free Edition).

## Data

`twin/data/nasa_battery_capacity_vs_cycle.csv`: capacity per discharge cycle for four cells (B0005, B0006, B0007, B0018), 636 rows, columns `cell_id`, `cycle`, `capacity_ah`, `ambient_temp_c`. Uploaded as the table `workspace.default.nasa_battery_capacity_vs_cycle`.

## What is in `databricks/`

| File | What it does |
|---|---|
| `queries.sql` | Cycle summary per cell, capacity retention with a window function (`FIRST_VALUE ... OVER (PARTITION BY ...)`), data quality checks (nulls, duplicate cycles, gaps, out-of-range values) |
| `04_cell_health_summary.py` | PySpark notebook: retention per cell, first cycle at or below 70 % of the initial capacity, result saved as the table `cell_health_summary` |

## Results

| Cell | Cycles | Initial capacity (Ah) | Lowest retention | First cycle at or below 70 % |
|---|---|---|---|---|
| B0005 | 168 | 1.8565 | 69.4 % | 162 |
| B0006 | 168 | 2.0353 | 56.7 % | 102 |
| B0007 | 168 | 1.8911 | 74.1 % | not reached |
| B0018 | 132 | 1.8550 | 72.3 % | not reached |

The data quality checks found no null values, duplicate cycles, cycle gaps or out-of-range capacities in any cell.

The cells age at clearly different rates: B0006 reaches 70 % about 60 cycles earlier than B0005, while B0007 and B0018 stay above 70 % until the end of their tests.

## Scope

- This is a learning exercise, not a production pipeline. The dataset is small (636 rows), so nothing here says anything about performance at scale.
- The NASA file is already a per-cycle summary, so the data was clean to begin with. The quality checks confirm that, but no real cleaning was needed.
- Databricks Free Edition is meant for learning: one small SQL warehouse, serverless compute only, restricted outbound internet.
- This exercise is separate from the Docker Compose system. The twin does not read from Databricks.
- The SoH model in the twin is trained on B0005 only. The results above show that B0006 ages much faster, so the model should not be assumed to generalise to other cells without testing.
