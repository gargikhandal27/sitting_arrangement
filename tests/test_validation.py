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


def test_repair_and_clean_students_duplicates_and_missing():
    # DataFrame with duplicates and missing values as shown in user bug report
    df = pd.DataFrame({
        "student_id": ["STU001", "STU001", "STU002", "STU003", ""],
        "roll_number": ["2024CSE001", "2024CSE001", "2024ECE002", "2024ECE002", "2024ME005"],
        "student_name": ["Alice", "Alice Dup", "", None, "Eve"],
        "batch": ["CSE", "CSE", "", "ECE", ""],
    })
    # Initial validation must fail
    is_valid, errors, _ = validate_students(df)
    assert is_valid is False
    assert len(errors) > 0

    # Auto-clean and repair
    repaired, actions = repair_and_clean_students(df)
    assert len(actions) > 0
    assert len(repaired) == 3  # Dup STU001 dropped, dup 2024ECE002 dropped

    # Repaired dataset MUST pass validation without errors
    is_valid_repaired, errors_repaired, clean_repaired = validate_students(repaired)
    assert is_valid_repaired is True
    assert len(errors_repaired) == 0
    assert len(clean_repaired) == 3

    # Check student names were auto-filled
    stu2_name = repaired.loc[repaired["student_id"] == "STU002", "student_name"].values[0]
    assert "Student" in stu2_name

    # Check batch was auto-filled/inferred
    last_batch = repaired.loc[repaired["roll_number"] == "2024ME005", "batch"].values[0]
    assert last_batch == "ME"


def test_repair_and_clean_classrooms():
    df = pd.DataFrame({
        "room_id": ["R101", "R101", "R102", ""],
        "room_name": ["Hall A", "Hall A Dup", "", "Lab B"],
        "rows": [5, 5, -2, "invalid"],
        "columns": [6, 6, 0, 8],
    })
    is_valid, errors, _ = validate_classrooms(df)
    assert is_valid is False

    repaired, actions = repair_and_clean_classrooms(df)
    assert len(actions) > 0
    # Duplicate R101 dropped -> 3 rooms left
    assert len(repaired) == 3

    # Validated
    is_valid_repaired, errors_repaired, clean_repaired = validate_classrooms(repaired)
    assert is_valid_repaired is True
    assert len(errors_repaired) == 0
    # Invalid rows corrected to default 5
    assert (repaired["rows"] > 0).all()
    assert (repaired["columns"] > 0).all()


def test_repair_and_clean_supervisors():
    df = pd.DataFrame({
        "supervisor_id": ["SUP01", "SUP01", "SUP02", ""],
        "supervisor_name": ["Dr. Smith", "Dr. Smith Dup", "", "Prof. Brown"],
    })
    is_valid, errors, _ = validate_supervisors(df)
    assert is_valid is False

    repaired, actions = repair_and_clean_supervisors(df)
    assert len(actions) > 0
    assert len(repaired) == 3

    is_valid_repaired, errors_repaired, clean_repaired = validate_supervisors(repaired)
    assert is_valid_repaired is True
    assert len(errors_repaired) == 0

