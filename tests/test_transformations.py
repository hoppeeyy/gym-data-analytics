"""
Unit tests for etl/transformations.py — run with:
    pytest tests/
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from etl.transformations import calculate_bmi, bmi_category, intensity_score


def test_calculate_bmi_normal_case():
    # 70kg, 175cm -> 70 / 1.75^2 = 22.86
    assert calculate_bmi(70, 175) == 22.86


def test_calculate_bmi_rounds_to_two_decimals():
    result = calculate_bmi(82.3, 178)
    assert result == round(result, 2)


def test_calculate_bmi_invalid_height_raises():
    try:
        calculate_bmi(70, 0)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_bmi_category_boundaries():
    assert bmi_category(18.0) == "Underweight"
    assert bmi_category(18.5) == "Normal"
    assert bmi_category(24.9) == "Normal"
    assert bmi_category(25.0) == "Overweight"
    assert bmi_category(29.9) == "Overweight"
    assert bmi_category(30.0) == "Obese"


def test_intensity_score_mapping():
    assert intensity_score("High") == 3
    assert intensity_score("Medium") == 2
    assert intensity_score("Low") == 1
    assert intensity_score("Unknown") == 1  # defaults to 1, same as glue_job.py


if __name__ == "__main__":
    # allow running without pytest installed: python tests/test_transformations.py
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
