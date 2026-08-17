-- ==========================================================
--  GymPulse: Amazon Athena Analysis Queries
--  Run against the Glue Data Catalog database created by
--  the Glue Crawler over s3://gym-analytics-bucket/processed/
--
--  NOTE: These queries are reconstructed from the aggregation
--  logic in etl/glue_job.py and the result columns consumed
--  in notebooks/visualization.ipynb. Adjust table/column names
--  to match your actual Glue Catalog schema if they differ.
-- ==========================================================

-- 1. BMI Distribution across members
-- (used by: bmi.columns -> bmi_category pie chart)
SELECT
    bmi_category,
    COUNT(*) AS member_count
FROM members
GROUP BY bmi_category
ORDER BY member_count DESC;


-- 2. Trainer Performance
-- (used by: trainer['trainer_name'] vs trainer['avg_calories_per_session'])
SELECT
    trainer_id,
    trainer_name,
    specialization,
    total_sessions_conducted,
    avg_calories_per_session,
    avg_intensity
FROM trainer_performance
ORDER BY avg_calories_per_session DESC;


-- 3. Workout Plan Effectiveness
-- (used by: workout['workout_plan'] vs workout['avg_calories_burned'])
SELECT
    workout_plan,
    COUNT(DISTINCT member_id)  AS members_enrolled,
    SUM(total_sessions)        AS total_sessions,
    ROUND(AVG(avg_duration_min), 2)     AS avg_duration_min,
    ROUND(AVG(avg_calories_burned), 2)  AS avg_calories_burned,
    ROUND(AVG(avg_intensity_score), 2)  AS avg_intensity_score
FROM workout_summary
GROUP BY workout_plan
ORDER BY avg_calories_burned DESC;


-- 4. Weekly Calorie Intake Trend
-- (used by: trend.groupby('week')['avg_weekly_calories'])
SELECT
    week,
    ROUND(AVG(avg_weekly_calories), 2) AS avg_weekly_calories
FROM weekly_diet_summary
GROUP BY week
ORDER BY week;


-- 5. Diet vs Workout Balance (per member)
-- (used by: diet['avg_daily_calorie_intake'] vs diet['avg_calories_burned_per_session'])
SELECT
    d.member_id,
    ROUND(AVG(d.avg_weekly_calories), 2) AS avg_daily_calorie_intake,
    ROUND(AVG(w.avg_calories_burned), 2) AS avg_calories_burned_per_session
FROM weekly_diet_summary d
JOIN workout_summary w
    ON d.member_id = w.member_id
GROUP BY d.member_id;


-- 6. Peak Workout Months
-- (used by: peak['workout_month'] vs peak['session_count'])
SELECT
    workout_month,
    workout_plan,
    session_count
FROM peak_hours
ORDER BY workout_month, session_count DESC;


-- 7. Top Members by Calories Burned
-- (used by: top.sort_values(by='avg_calories_burned').head(10))
SELECT
    m.member_id,
    m.name,
    ROUND(AVG(w.avg_calories_burned), 2) AS avg_calories_burned
FROM members m
JOIN workout_summary w
    ON m.member_id = w.member_id
GROUP BY m.member_id, m.name
ORDER BY avg_calories_burned DESC
LIMIT 10;


-- 8. Average Protein vs Average Calories by Meal Type
-- (used by: protein['meal_type'] vs protein['avg_protein'] / protein['avg_calories'])
SELECT
    meal_type,
    ROUND(AVG(protein_g), 2)        AS avg_protein,
    ROUND(AVG(calories_intake), 2)  AS avg_calories
FROM diet_logs
GROUP BY meal_type
ORDER BY avg_calories DESC;
