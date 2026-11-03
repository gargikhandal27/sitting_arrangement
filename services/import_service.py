"""
Import service – reads CSV/Excel, validates, and saves to database.
"""
from typing import Tuple
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from database.models import Student, Classroom, Seat, Supervisor
from services.validation_service import (
    validate_students,
    validate_classrooms,
    validate_supervisors,
)


def read_uploaded_file(uploaded_file) -> pd.DataFrame:
    """Read CSV or Excel file into a DataFrame."""
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    elif name.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file)
    else:
        raise ValueError("Unsupported file type. Please upload CSV or Excel (.xlsx).")


def import_students(db: Session, df: pd.DataFrame, replace_existing: bool = False) -> Tuple[bool, str, int]:
    """
    Validate and import students.
    Returns: (success, message, count_imported)
    """
    is_valid, errors, clean_df = validate_students(df)
    if not is_valid:
        return False, "Validation failed:\n- " + "\n- ".join(errors), 0

    if replace_existing:
        db.execute(delete(Student))
        db.flush()

    imported = 0
    skipped = 0
    for _, row in clean_df.iterrows():
        existing = db.scalar(select(Student).where(Student.student_id == row["student_id"]))
        if existing:
            skipped += 1
            continue
        student = Student(
            student_id=row["student_id"],
            roll_number=row["roll_number"],
            student_name=row["student_name"],
            batch=row["batch"],
            is_active=True,
        )
        db.add(student)
        imported += 1

    db.commit()
    msg = f"Successfully imported {imported} student(s)."
    if skipped:
        msg += f" Skipped {skipped} duplicate student_id(s)."
    return True, msg, imported


def import_classrooms(db: Session, df: pd.DataFrame, replace_existing: bool = False) -> Tuple[bool, str, int]:
    is_valid, errors, clean_df = validate_classrooms(df)
    if not is_valid:
        return False, "Validation failed:\n- " + "\n- ".join(errors), 0

    if replace_existing:
        db.execute(delete(Classroom))
        db.flush()

    imported = 0
    skipped = 0
    for _, row in clean_df.iterrows():
        existing = db.scalar(select(Classroom).where(Classroom.room_id == row["room_id"]))
        if existing:
            skipped += 1
            continue

        classroom = Classroom(
            room_id=row["room_id"],
            room_name=row["room_name"],
            rows=int(row["rows"]),
            columns=int(row["columns"]),
            is_available=bool(row["is_available"]),
            layout_source="csv",
        )
        db.add(classroom)
        db.flush()  # get classroom.id

        # Auto-generate seats for the grid
        for r in range(1, int(row["rows"]) + 1):
            for c in range(1, int(row["columns"]) + 1):
                seat = Seat(
                    classroom_id=classroom.id,
                    seat_code=f"R{r}C{c}",
                    row_number=r,
                    column_number=c,
                    is_available=True,
                    is_confirmed=True,
                    detection_source="csv",
                )
                db.add(seat)

        imported += 1

    db.commit()
    msg = f"Successfully imported {imported} classroom(s) and generated seats."
    if skipped:
        msg += f" Skipped {skipped} duplicate room_id(s)."
    return True, msg, imported


def import_supervisors(db: Session, df: pd.DataFrame, replace_existing: bool = False) -> Tuple[bool, str, int]:
    is_valid, errors, clean_df = validate_supervisors(df)
    if not is_valid:
        return False, "Validation failed:\n- " + "\n- ".join(errors), 0

    if replace_existing:
        db.execute(delete(Supervisor))
        db.flush()

    imported = 0
    skipped = 0
    for _, row in clean_df.iterrows():
        existing = db.scalar(select(Supervisor).where(Supervisor.supervisor_id == row["supervisor_id"]))
        if existing:
            skipped += 1
            continue
        sup = Supervisor(
            supervisor_id=row["supervisor_id"],
            supervisor_name=row["supervisor_name"],
            is_available=bool(row["is_available"]),
        )
        db.add(sup)
        imported += 1

    db.commit()
    msg = f"Successfully imported {imported} supervisor(s)."
    if skipped:
        msg += f" Skipped {skipped} duplicate supervisor_id(s)."
    return True, msg, imported
