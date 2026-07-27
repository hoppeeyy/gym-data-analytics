-- BMI Distribution

SELECT bmi_category, COUNT(*) AS members
FROM members
GROUP BY bmi_category;

-- Workout Effectiveness

SELECT workout_plan,
       AVG(calories_burned) AS avg_calories
FROM workout_logs
GROUP BY workout_plan
ORDER BY avg_calories DESC;

-- Diet vs Workout

SELECT m.member_id,
       AVG(d.calories_intake) AS avg_intake,
       AVG(w.calories_burned) AS avg_burned
FROM members m
JOIN diet_logs d
ON m.member_id = d.member_id
JOIN workout_logs w
ON m.member_id = w.member_id
GROUP BY m.member_id;

-- Trainer Leaderboard

SELECT trainer_id,
       AVG(calories_burned) AS avg_burn
FROM trainer_performance
GROUP BY trainer_id
ORDER BY avg_burn DESC;

-- Peak Workout Months

SELECT workout_month,
       COUNT(*) AS sessions
FROM workout_logs
GROUP BY workout_month
ORDER BY sessions DESC;

-- Weekly Diet Trend

SELECT week,
       AVG(avg_calories)
FROM weekly_diet_summary
GROUP BY week;
