"""
==========================================================
  Pure-Python Transformation Logic — GymPulse
  Project: 23/IT/040 & 23/IT/056 | DTU
==========================================================

These functions mirror the PySpark feature-engineering logic
inside `etl/glue_job.py` (BMI, BMI category, intensity score),
but written as plain Python so they can be unit tested locally
without spinning up a Spark/Glue environment.

They are intentionally kept in sync with glue_job.py — if you
change a formula there, update it here too (see tests/).
"""


def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    """BMI = weight(kg) / height(m)^2, rounded to 2 decimals."""
    if height_cm <= 0:
        raise ValueError("height_cm must be > 0")
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 2)


def bmi_category(bmi: float) -> str:
    """Bucket a BMI value into a category (matches glue_job.py)."""
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25.0:
        return "Normal"
    if bmi < 30.0:
        return "Overweight"
    return "Obese"


def intensity_score(intensity: str) -> int:
    """Map workout intensity (Low/Medium/High) to a numeric score."""
    return {"High": 3, "Medium": 2}.get(intensity, 1)
