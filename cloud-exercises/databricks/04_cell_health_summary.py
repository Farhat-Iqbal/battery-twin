# Databricks notebook: 04_cell_health_summary
# Reads the NASA battery table, computes capacity retention per cell and the first cycle
# at or below 70% of the initial capacity, and saves the result as a table.
from pyspark.sql import functions as F, Window

df = spark.table("workspace.default.nasa_battery_capacity_vs_cycle")

w = Window.partitionBy("cell_id").orderBy("cycle")
df = (df
      .withColumn("initial_capacity_ah", F.first("capacity_ah").over(w))
      .withColumn("retention_pct",
                  F.round(100 * F.col("capacity_ah") / F.col("initial_capacity_ah"), 2)))

# first cycle where the cell falls to 70% of its initial capacity (common end-of-life threshold)
eol = (df.filter(F.col("retention_pct") <= 70)
         .groupBy("cell_id")
         .agg(F.min("cycle").alias("first_cycle_at_or_below_70pct")))

summary = (df.groupBy("cell_id")
             .agg(F.count("*").alias("cycles"),
                  F.round(F.max("initial_capacity_ah"), 4).alias("initial_capacity_ah"),
                  F.round(F.min("capacity_ah"), 4).alias("min_capacity_ah"),
                  F.round(F.min("retention_pct"), 1).alias("lowest_retention_pct"))
             .join(eol, "cell_id", "left")
             .orderBy("cell_id"))

summary.write.mode("overwrite").saveAsTable("workspace.default.cell_health_summary")
display(spark.table("workspace.default.cell_health_summary"))
