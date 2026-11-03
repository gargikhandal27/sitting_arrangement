"""Unit tests for validation service."""
import pandas as pd
import pytest
from services.validation_service import (
    validate_students,
    validate_classrooms,
    validate_supervisors,
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
