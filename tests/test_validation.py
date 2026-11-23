"""Unit tests for validation service."""
import pandas as pd
import pytest
from services.validation_service import (
    validate_students,
    validate_classrooms,
    validate_supervisors,
    repair_and_clean_students,
    repair_and_clean_classrooms,
    repair_and_clean_supervisors,
)


def test_valid_students():
    df = pd.DataFrame({
        "student_id": ["ST001", "ST002"],
        "roll_number": ["101", "102"],
        "student_name": ["A", "B"],
        "batch": ["CSE_A", "CSE_B"],
    })
    ok, errors, clean = validate_students(df)
    assert ok is True
    assert len(errors) == 0
    assert len(clean) == 2


def test_missing_column_students():
    df = pd.DataFrame({
        "student_id": ["ST001"],
        "roll_number": ["101"],
        "student_name": ["A"],
        # batch missing
    })
    ok, errors, _ = validate_students(df)
    assert ok is False
    assert any("batch" in e.lower() for e in errors)


def test_duplicate_student_id():
    df = pd.DataFrame({
        "student_id": ["ST001", "ST001"],
        "roll_number": ["101", "102"],
        "student_name": ["A", "B"],
        "batch": ["CSE_A", "CSE_A"],
    })
    ok, errors, _ = validate_students(df)
    assert ok is False
    assert any("duplicate" in e.lower() for e in errors)


def test_valid_classrooms():
    df = pd.DataFrame({
        "room_id": ["R1"],
        "room_name": ["Hall"],
        "rows": [3],
        "columns": [4],
        "is_available": [True],
    })
    ok, errors, clean = validate_classrooms(df)
    assert ok is True
    assert len(clean) == 1


def test_valid_supervisors():
    df = pd.DataFrame({
        "supervisor_id": ["SUP1"],
        "supervisor_name": ["Dr. X"],
        "is_available": [True],
    })
    ok, errors, clean = validate_supervisors(df)
    assert ok is True


def test_repair_and_clean_students():
    # Messy data with missing names, batches, duplicate IDs & roll numbers, and blank rows
    messy_df = pd.DataFrame({
        "student_id": ["STU001", "STU002", "STU001", "STU003", "", None],
        "roll_number": ["2024CSE001", "2024CSE002", "2024CSE003", "2024CSE001", "2024ECE005", "  "],
        "student_name": ["Alice", None, "Charlie", "", "Eve", "  "],
        "batch": ["CSE", None, "CSE", "", "ECE", "  "],
    })
    clean_df, actions = repair_and_clean_students(messy_df)

    assert len(actions) > 0
    # Blank row should be removed
    assert len(clean_df) <= 4

    # Repaired dataframe MUST pass validate_students with 0 errors
    ok, errors, validated = validate_students(clean_df)
    assert ok is True, f"Validation failed with errors: {errors}"
    assert len(errors) == 0

    # Ensure no duplicates remain
    assert clean_df["student_id"].duplicated().sum() == 0
    assert clean_df["roll_number"].duplicated().sum() == 0

    # Ensure missing names were filled
    assert (clean_df["student_name"] == "").sum() == 0
    assert any("Student" in name for name in clean_df["student_name"])


def test_repair_and_clean_classrooms():
    messy_df = pd.DataFrame({
        "room_id": ["R101", "R102", "R101", "", None],
        "room_name": ["Main Hall", "", "Main Hall Duplicate", "  ", ""],
        "rows": [5, -2, "invalid", 4, 3],
        "columns": [6, 0, None, 5, 4],
        "is_available": [True, "yes", False, True, "1"],
    })
    clean_df, actions = repair_and_clean_classrooms(messy_df)

    assert len(actions) > 0
    ok, errors, validated = validate_classrooms(clean_df)
    assert ok is True, f"Validation failed with errors: {errors}"
    assert len(errors) == 0
    assert clean_df["room_id"].duplicated().sum() == 0
    assert (clean_df["rows"] > 0).all()
    assert (clean_df["columns"] > 0).all()


def test_repair_and_clean_supervisors():
    messy_df = pd.DataFrame({
        "supervisor_id": ["SUP01", "SUP02", "SUP01", "", None],
        "supervisor_name": ["Dr. Smith", "", "Duplicate Smith", "Prof. Jane", ""],
        "is_available": [True, False, True, "yes", "0"],
    })
    clean_df, actions = repair_and_clean_supervisors(messy_df)

    assert len(actions) > 0
    ok, errors, validated = validate_supervisors(clean_df)
    assert ok is True, f"Validation failed with errors: {errors}"
    assert len(errors) == 0
    assert clean_df["supervisor_id"].duplicated().sum() == 0
    assert (clean_df["supervisor_name"] == "").sum() == 0

