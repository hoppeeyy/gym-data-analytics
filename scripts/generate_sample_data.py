"""
==========================================================
  Synthetic Data Generator — GymPulse
  Project: 23/IT/040 & 23/IT/056 | DTU
==========================================================

Generates realistic raw CSVs (members, workout_logs, diet_logs,
trainers) that match the exact schema expected by
`etl/glue_job.py`. Useful for:

  - Testing the Glue ETL job locally before deploying to AWS
  - Populating s3://<your-bucket>/raw/ with data at scale
  - Reproducing the "250+ gym members" dataset used in this
    project without needing the original (private) data

Usage:
    python scripts/generate_sample_data.py --members 250 --out data/raw

Output (written to --out):
    members.csv
    trainers.csv
    workout_logs.csv
    diet_logs.csv
"""

import argparse
import csv
import random
from datetime import date, timedelta

FIRST_NAMES = [
    "Aarav", "Diya", "Kabir", "Ishita", "Rohit", "Sneha", "Aditya", "Meera",
    "Karan", "Neha", "Siddharth", "Tanvi", "Rahul", "Pooja", "Varun", "Ananya",
    "Vikram", "Priya", "Arjun", "Simran", "Nikhil", "Kavya", "Yash", "Riya",
    "Manav", "Anjali", "Dev", "Shreya", "Amit", "Isha",
]
LAST_NAMES = [
    "Sharma", "Patel", "Malhotra", "Verma", "Yadav", "Reddy", "Kumar", "Iyer",
    "Joshi", "Gupta", "Rao", "Bhatt", "Chatterjee", "Menon", "Saxena", "Kapoor",
    "Singh", "Nair", "Desai", "Kaur",
]
WORKOUT_PLANS = ["Strength", "Cardio", "Yoga", "HIIT", "CrossFit", "Bodybuilding", "Weight Loss"]
INTENSITIES = ["Low", "Medium", "High"]
MEAL_TYPES = ["Breakfast", "Lunch", "Dinner", "Snack"]
SPECIALIZATIONS = [
    "Strength Training", "Cardio & HIIT", "CrossFit", "Yoga & Flexibility",
    "Weight Loss", "Bodybuilding",
]

random.seed(42)  # reproducible output


def random_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def gen_trainers(n=6):
    rows = []
    for i in range(1, n + 1):
        rows.append({
            "trainer_id": f"T{i:03d}",
            "trainer_name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            "specialization": SPECIALIZATIONS[(i - 1) % len(SPECIALIZATIONS)],
        })
    return rows


def gen_members(n, trainer_ids):
    rows = []
    join_start, join_end = date(2024, 1, 1), date(2025, 6, 30)
    for i in range(1, n + 1):
        gender = random.choice(["Male", "Female"])
        height = random.randint(155, 190) if gender == "Male" else random.randint(148, 175)
        weight = round(random.uniform(55, 100) if gender == "Male" else random.uniform(45, 85), 1)
        rows.append({
            "member_id": f"M{i:04d}",
            "name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            "age": random.randint(18, 55),
            "gender": gender,
            "weight_kg": weight,
            "height_cm": height,
            "join_date": random_date(join_start, join_end).isoformat(),
            "trainer_id": random.choice(trainer_ids),
        })
    return rows


def gen_workout_logs(members, logs_per_member=(8, 20)):
    rows = []
    log_start, log_end = date(2025, 1, 1), date(2025, 6, 30)
    log_id = 1
    for m in members:
        for _ in range(random.randint(*logs_per_member)):
            intensity = random.choice(INTENSITIES)
            base_cal = {"Low": 180, "Medium": 320, "High": 480}[intensity]
            rows.append({
                "log_id": f"L{log_id:05d}",
                "member_id": m["member_id"],
                "workout_date": random_date(log_start, log_end).isoformat(),
                "workout_plan": random.choice(WORKOUT_PLANS),
                "duration_min": random.randint(30, 90),
                "calories_burned": base_cal + random.randint(-40, 60),
                "intensity": intensity,
            })
            log_id += 1
    return rows


def gen_diet_logs(members, logs_per_member=(10, 25)):
    rows = []
    log_start, log_end = date(2025, 1, 1), date(2025, 6, 30)
    diet_id = 1
    for m in members:
        for _ in range(random.randint(*logs_per_member)):
            meal = random.choice(MEAL_TYPES)
            rows.append({
                "diet_id": f"D{diet_id:05d}",
                "member_id": m["member_id"],
                "log_date": random_date(log_start, log_end).isoformat(),
                "meal_type": meal,
                "calories_intake": random.randint(250, 750),
                "protein_g": random.randint(15, 50),
                "carbs_g": random.randint(30, 80),
                "fat_g": random.randint(6, 22),
            })
            diet_id += 1
    return rows


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"   Wrote {len(rows):>6} rows -> {path}")


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic GymPulse raw data.")
    parser.add_argument("--members", type=int, default=250, help="Number of gym members to generate")
    parser.add_argument("--trainers", type=int, default=6, help="Number of trainers to generate")
    parser.add_argument("--out", type=str, default="data/raw", help="Output directory for CSVs")
    args = parser.parse_args()

    import os
    os.makedirs(args.out, exist_ok=True)

    print(f"Generating synthetic data for {args.members} members...")

    trainers = gen_trainers(args.trainers)
    members = gen_members(args.members, [t["trainer_id"] for t in trainers])
    workouts = gen_workout_logs(members)
    diets = gen_diet_logs(members)

    write_csv(f"{args.out}/trainers.csv", trainers,
              ["trainer_id", "trainer_name", "specialization"])
    write_csv(f"{args.out}/members.csv", members,
              ["member_id", "name", "age", "gender", "weight_kg", "height_cm", "join_date", "trainer_id"])
    write_csv(f"{args.out}/workout_logs.csv", workouts,
              ["log_id", "member_id", "workout_date", "workout_plan", "duration_min", "calories_burned", "intensity"])
    write_csv(f"{args.out}/diet_logs.csv", diets,
              ["diet_id", "member_id", "log_date", "meal_type", "calories_intake", "protein_g", "carbs_g", "fat_g"])

    print("\nDone. Upload these files to s3://<your-bucket>/raw/ before running the Glue job.")


if __name__ == "__main__":
    main()
