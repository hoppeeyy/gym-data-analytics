-- ==========================================================
--  GymPulse: Glue Data Catalog / Athena Table Definitions
--
--  Run these once (or let the AWS Glue Crawler generate them
--  automatically) so that sql/athena_queries.sql has tables
--  to query. Column names/types mirror the DataFrames written
--  out in etl/glue_job.py's write_parquet() calls.
--
--  Replace `gym_analytics_db` and the S3 bucket name with your
--  own database / bucket before running.
-- ==========================================================

CREATE DATABASE IF NOT EXISTS gym_analytics_db;

-- 1. members (cleaned + BMI features)
CREATE EXTERNAL TABLE IF NOT EXISTS gym_analytics_db.members (
    member_id     STRING,
    name          STRING,
    age           INT,
    gender        STRING,
    weight_kg     DOUBLE,
    height_cm     DOUBLE,
    join_date     DATE,
    trainer_id    STRING,
    bmi           DOUBLE,
    bmi_category  STRING
)
STORED AS PARQUET
LOCATION 's3://gym-analytics-bucket/processed/members/';

-- 2. workout_logs (cleaned + week/month/year + intensity_score)
CREATE EXTERNAL TABLE IF NOT EXISTS gym_analytics_db.workout_logs (
    log_id           STRING,
    member_id        STRING,
    workout_date     DATE,
    workout_plan     STRING,
    duration_min     INT,
    calories_burned  INT,
    intensity        STRING,
    workout_week     INT,
    workout_month    INT,
    workout_year     INT,
    intensity_score  INT
)
STORED AS PARQUET
LOCATION 's3://gym-analytics-bucket/processed/workout_logs/';

-- 3. diet_logs (cleaned)
CREATE EXTERNAL TABLE IF NOT EXISTS gym_analytics_db.diet_logs (
    diet_id          STRING,
    member_id        STRING,
    log_date         DATE,
    meal_type        STRING,
    calories_intake  INT,
    protein_g        INT,
    carbs_g          INT,
    fat_g            INT
)
STORED AS PARQUET
LOCATION 's3://gym-analytics-bucket/processed/diet_logs/';

-- 4. weekly_diet_summary
CREATE EXTERNAL TABLE IF NOT EXISTS gym_analytics_db.weekly_diet_summary (
    member_id            STRING,
    week                 INT,
    avg_weekly_calories  DOUBLE,
    avg_protein_g        DOUBLE,
    avg_carbs_g          DOUBLE,
    avg_fat_g            DOUBLE
)
STORED AS PARQUET
LOCATION 's3://gym-analytics-bucket/processed/weekly_diet_summary/';

-- 5. workout_summary
CREATE EXTERNAL TABLE IF NOT EXISTS gym_analytics_db.workout_summary (
    member_id             STRING,
    workout_plan          STRING,
    total_sessions        BIGINT,
    avg_duration_min       DOUBLE,
    avg_calories_burned    DOUBLE,
    avg_intensity_score    DOUBLE
)
STORED AS PARQUET
LOCATION 's3://gym-analytics-bucket/processed/workout_summary/';

-- 6. peak_hours (peak workout months by plan)
CREATE EXTERNAL TABLE IF NOT EXISTS gym_analytics_db.peak_hours (
    workout_month  INT,
    workout_plan   STRING,
    session_count  BIGINT
)
STORED AS PARQUET
LOCATION 's3://gym-analytics-bucket/processed/peak_hours/';

-- 7. trainer_performance
CREATE EXTERNAL TABLE IF NOT EXISTS gym_analytics_db.trainer_performance (
    trainer_id                 STRING,
    total_sessions_conducted   BIGINT,
    avg_calories_per_session   DOUBLE,
    avg_intensity              DOUBLE,
    trainer_name               STRING,
    specialization             STRING
)
STORED AS PARQUET
LOCATION 's3://gym-analytics-bucket/processed/trainer_performance/';

-- NOTE: If you use the Glue Crawler instead of manual DDL, point it at
-- s3://<your-bucket>/processed/ with "Create a single schema for each
-- S3 path" so it produces one table per subfolder, matching the names
-- above automatically.
