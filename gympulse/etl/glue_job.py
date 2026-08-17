"""
==========================================================
  Gym Performance & Diet Analytics Pipeline
  AWS Glue ETL Script
  Project: 23/IT/040 & 23/IT/056 | DTU
==========================================================

This script is deployed as an AWS Glue Job.
It reads raw CSV files from S3, performs transformations,
and writes cleaned data back to S3 (for Athena) and
optionally to Redshift.

S3 Structure Expected:
  s3://gym-analytics-bucket/raw/members.csv
  s3://gym-analytics-bucket/raw/workout_logs.csv
  s3://gym-analytics-bucket/raw/diet_logs.csv
  s3://gym-analytics-bucket/raw/trainers.csv

Output:
  s3://gym-analytics-bucket/processed/members/
  s3://gym-analytics-bucket/processed/workout_logs/
  s3://gym-analytics-bucket/processed/diet_logs/
  s3://gym-analytics-bucket/processed/weekly_summary/
"""

import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType
from awsglue.dynamicframe import DynamicFrame

# ── Job Init ──────────────────────────────────────────────
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc   = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job   = Job(glueContext)
job.init(args['JOB_NAME'], args)

S3_BUCKET  = "s3://gym-analytics-bucket"
RAW_PATH   = f"{S3_BUCKET}/raw"
PROC_PATH  = f"{S3_BUCKET}/processed"

# ============================================================
# 1. INGEST RAW DATA FROM S3
# ============================================================

def read_csv(path):
    return spark.read.option("header", "true") \
                     .option("inferSchema", "true") \
                     .csv(path)

members      = read_csv(f"{RAW_PATH}/members.csv")
workout_logs = read_csv(f"{RAW_PATH}/workout_logs.csv")
diet_logs    = read_csv(f"{RAW_PATH}/diet_logs.csv")
trainers     = read_csv(f"{RAW_PATH}/trainers.csv")

print("✅ Raw data loaded successfully.")
print(f"   Members: {members.count()} rows")
print(f"   Workouts: {workout_logs.count()} rows")
print(f"   Diet Logs: {diet_logs.count()} rows")

# ============================================================
# 2. DATA CLEANING
# ============================================================

# --- Drop rows with critical nulls ---
members      = members.dropna(subset=["member_id", "name", "weight_kg", "height_cm"])
workout_logs = workout_logs.dropna(subset=["log_id", "member_id", "workout_date"])
diet_logs    = diet_logs.dropna(subset=["diet_id", "member_id", "log_date"])

# --- Standardize date formats ---
workout_logs = workout_logs.withColumn(
    "workout_date", F.to_date(F.col("workout_date"), "yyyy-MM-dd")
)
diet_logs = diet_logs.withColumn(
    "log_date", F.to_date(F.col("log_date"), "yyyy-MM-dd")
)
members = members.withColumn(
    "join_date", F.to_date(F.col("join_date"), "yyyy-MM-dd")
)

# --- Remove duplicates ---
members      = members.dropDuplicates(["member_id"])
workout_logs = workout_logs.dropDuplicates(["log_id"])
diet_logs    = diet_logs.dropDuplicates(["diet_id"])

print("✅ Data cleaned — nulls dropped, dates standardized, duplicates removed.")

# ============================================================
# 3. FEATURE ENGINEERING
# ============================================================

# --- Calculate BMI for each member ---
# BMI = weight(kg) / (height(m))^2
members = members.withColumn(
    "bmi",
    F.round(
        F.col("weight_kg") / ((F.col("height_cm") / 100) ** 2),
        2
    )
)

# --- BMI Category ---
members = members.withColumn(
    "bmi_category",
    F.when(F.col("bmi") < 18.5, "Underweight")
     .when((F.col("bmi") >= 18.5) & (F.col("bmi") < 25.0), "Normal")
     .when((F.col("bmi") >= 25.0) & (F.col("bmi") < 30.0), "Overweight")
     .otherwise("Obese")
)

# --- Extract Week & Month from workout_date ---
workout_logs = workout_logs.withColumn("workout_week", F.weekofyear("workout_date"))
workout_logs = workout_logs.withColumn("workout_month", F.month("workout_date"))
workout_logs = workout_logs.withColumn("workout_year", F.year("workout_date"))

# --- Intensity Score (numeric) ---
workout_logs = workout_logs.withColumn(
    "intensity_score",
    F.when(F.col("intensity") == "High", 3)
     .when(F.col("intensity") == "Medium", 2)
     .otherwise(1)
)

print("✅ Feature engineering done — BMI, intensity score, week/month extracted.")

# ============================================================
# 4. AGGREGATIONS
# ============================================================

# --- Weekly Calorie Intake per Member ---
weekly_diet = diet_logs.groupBy("member_id", F.weekofyear("log_date").alias("week")) \
    .agg(
        F.round(F.avg("calories_intake"), 2).alias("avg_weekly_calories"),
        F.round(F.avg("protein_g"), 2).alias("avg_protein_g"),
        F.round(F.avg("carbs_g"), 2).alias("avg_carbs_g"),
        F.round(F.avg("fat_g"), 2).alias("avg_fat_g"),
    )

# --- Workout Summary per Member ---
workout_summary = workout_logs.groupBy("member_id", "workout_plan") \
    .agg(
        F.count("log_id").alias("total_sessions"),
        F.round(F.avg("duration_min"), 2).alias("avg_duration_min"),
        F.round(F.avg("calories_burned"), 2).alias("avg_calories_burned"),
        F.round(F.avg("intensity_score"), 2).alias("avg_intensity_score"),
    )

# --- Peak Gym Hours (by month) ---
peak_hours = workout_logs.groupBy("workout_month", "workout_plan") \
    .agg(F.count("log_id").alias("session_count")) \
    .orderBy("workout_month", F.desc("session_count"))

# --- Trainer Performance: avg calories burned by trainer ---
trainer_perf = workout_logs \
    .join(members.select("member_id", "trainer_id"), on="member_id", how="left") \
    .groupBy("trainer_id") \
    .agg(
        F.count("log_id").alias("total_sessions_conducted"),
        F.round(F.avg("calories_burned"), 2).alias("avg_calories_per_session"),
        F.round(F.avg("intensity_score"), 2).alias("avg_intensity"),
    ) \
    .join(trainers.select("trainer_id", "trainer_name", "specialization"), on="trainer_id", how="left")

print("✅ Aggregations complete — weekly diet, workout summary, peak hours, trainer performance.")

# ============================================================
# 5. WRITE PROCESSED DATA TO S3
# ============================================================

def write_parquet(df, name):
    df.write.mode("overwrite").parquet(f"{PROC_PATH}/{name}/")
    print(f"   ✅ Written: {PROC_PATH}/{name}/")

print("\n📤 Writing processed data to S3...")
write_parquet(members,         "members")
write_parquet(workout_logs,    "workout_logs")
write_parquet(diet_logs,       "diet_logs")
write_parquet(weekly_diet,     "weekly_diet_summary")
write_parquet(workout_summary, "workout_summary")
write_parquet(peak_hours,      "peak_hours")
write_parquet(trainer_perf,    "trainer_performance")

print("\n🎉 ETL Pipeline completed successfully!")
job.commit()
