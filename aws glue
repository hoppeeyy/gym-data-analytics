from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

spark = SparkSession.builder \
    .appName("Gym Analytics ETL") \
    .getOrCreate()

# -----------------------------
# Read Raw Data from S3
# -----------------------------

members_df = spark.read.option("header", True).csv(
    "s3://gym-analytics-bucket/raw/members.csv",
    inferSchema=True
)

workout_df = spark.read.option("header", True).csv(
    "s3://gym-analytics-bucket/raw/workout_logs.csv",
    inferSchema=True
)

diet_df = spark.read.option("header", True).csv(
    "s3://gym-analytics-bucket/raw/diet_logs.csv",
    inferSchema=True
)

# -----------------------------
# Data Cleaning
# -----------------------------

members_df = members_df.dropna()
workout_df = workout_df.dropna()
diet_df = diet_df.dropna()

members_df = members_df.dropDuplicates()
workout_df = workout_df.dropDuplicates()
diet_df = diet_df.dropDuplicates()

# -----------------------------
# Date Standardization
# -----------------------------

members_df = members_df.withColumn(
    "join_date",
    to_date(col("join_date"), "yyyy-MM-dd")
)

workout_df = workout_df.withColumn(
    "workout_date",
    to_date(col("workout_date"), "yyyy-MM-dd")
)

diet_df = diet_df.withColumn(
    "log_date",
    to_date(col("log_date"), "yyyy-MM-dd")
)

# -----------------------------
# BMI Calculation
# -----------------------------

members_df = members_df.withColumn(
    "bmi",
    round(
        col("weight_kg") /
        pow(col("height_cm") / 100, 2),
        2
    )
)

members_df = members_df.withColumn(
    "bmi_category",
    when(col("bmi") < 18.5, "Underweight")
    .when((col("bmi") >= 18.5) & (col("bmi") < 25), "Normal")
    .when((col("bmi") >= 25) & (col("bmi") < 30), "Overweight")
    .otherwise("Obese")
)

# -----------------------------
# Workout Feature Engineering
# -----------------------------

workout_df = workout_df.withColumn(
    "intensity_score",
    when(col("intensity") == "High", 3)
    .when(col("intensity") == "Medium", 2)
    .otherwise(1)
)

workout_df = workout_df.withColumn(
    "workout_week",
    weekofyear(col("workout_date"))
)

workout_df = workout_df.withColumn(
    "workout_month",
    month(col("workout_date"))
)

# -----------------------------
# Weekly Diet Summary
# -----------------------------

weekly_diet_summary = diet_df \
    .withColumn("week", weekofyear(col("log_date"))) \
    .groupBy("member_id", "week") \
    .agg(
        round(avg("calories_intake"), 2).alias("avg_calories"),
        round(avg("protein_g"), 2).alias("avg_protein")
    )

# -----------------------------
# Workout Summary
# -----------------------------

workout_summary = workout_df.groupBy(
    "workout_plan"
).agg(
    round(avg("calories_burned"), 2).alias("avg_calories_burned"),
    round(avg("duration_min"), 2).alias("avg_duration"),
    round(avg("intensity_score"), 2).alias("avg_intensity")
)

# -----------------------------
# Trainer Performance
# -----------------------------

trainer_performance = members_df.join(
    workout_df,
    "member_id"
).groupBy(
    "trainer_id"
).agg(
    count("*").alias("total_sessions"),
    round(avg("calories_burned"), 2).alias("avg_calories_burned")
)

# -----------------------------
# Write Processed Data
# -----------------------------

members_df.write.mode("overwrite").parquet(
    "s3://gym-analytics-bucket/processed/members/"
)

workout_df.write.mode("overwrite").parquet(
    "s3://gym-analytics-bucket/processed/workouts/"
)

diet_df.write.mode("overwrite").parquet(
    "s3://gym-analytics-bucket/processed/diets/"
)

weekly_diet_summary.write.mode("overwrite").parquet(
    "s3://gym-analytics-bucket/processed/weekly_diet_summary/"
)

workout_summary.write.mode("overwrite").parquet(
    "s3://gym-analytics-bucket/processed/workout_summary/"
)

trainer_performance.write.mode("overwrite").parquet(
    "s3://gym-analytics-bucket/processed/trainer_performance/"
)

print("ETL Pipeline Completed Successfully")
