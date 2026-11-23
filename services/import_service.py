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
    Validate and import students with high-performance bulk operations.
    Returns: (success, message, count_imported)
    """
    is_valid, errors, clean_df = validate_students(df)
    if not is_valid:
        return False, "Validation failed:\n- " + "\n- ".join(errors), 0

    if replace_existing:
        db.execute(delete(Student))
        db.flush()
        existing_ids = set()
    else:
        existing_ids = set(db.scalars(select(Student.student_id)).all())

    imported = 0
    skipped = 0
    new_students = []

    for row in clean_df.itertuples(index=False):
        sid = str(row.student_id)
        if sid in existing_ids:
            skipped += 1
            continue
        new_students.append(
            Student(
                student_id=sid,
                roll_number=str(row.roll_number),
                student_name=str(row.student_name),
                batch=str(row.batch),
                is_active=True,
            )
        )
        existing_ids.add(sid)
        imported += 1

    if new_students:
        db.add_all(new_students)
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
        existing_ids = set()
    else:
        existing_ids = set(db.scalars(select(Classroom.room_id)).all())

    imported = 0
    skipped = 0
    all_seats = []

    for row in clean_df.itertuples(index=False):
        rid = str(row.room_id)
        if rid in existing_ids:
            skipped += 1
            continue

        classroom = Classroom(
            room_id=rid,
            room_name=str(row.room_name),
            rows=int(row.rows),
            columns=int(row.columns),
            is_available=bool(row.is_available),
            layout_source="csv",
        )
        db.add(classroom)
        db.flush()  # get classroom.id
        existing_ids.add(rid)

        # Bulk generate seats for the grid
        for r in range(1, int(row.rows) + 1):
            for c in range(1, int(row.columns) + 1):
                all_seats.append(
                    Seat(
                        classroom_id=classroom.id,
                        seat_code=f"R{r}C{c}",
                        row_number=r,
                        column_number=c,
                        is_available=True,
                        is_confirmed=True,
                        detection_source="csv",
                    )
                )
        imported += 1

    if all_seats:
        db.add_all(all_seats)

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
        existing_ids = set()
    else:
        existing_ids = set(db.scalars(select(Supervisor.supervisor_id)).all())

    imported = 0
    skipped = 0
    new_sups = []

    for row in clean_df.itertuples(index=False):
        sup_id = str(row.supervisor_id)
        if sup_id in existing_ids:
            skipped += 1
            continue
        new_sups.append(
            Supervisor(
                supervisor_id=sup_id,
                supervisor_name=str(row.supervisor_name),
                is_available=bool(row.is_available),
            )
        )
        existing_ids.add(sup_id)
        imported += 1

    if new_sups:
        db.add_all(new_sups)

    db.commit()
    msg = f"Successfully imported {imported} supervisor(s)."
    if skipped:
        msg += f" Skipped {skipped} duplicate supervisor_id(s)."
    return True, msg, imported
    msg = f"Successfully imported {imported} supervisor(s)."
    if skipped:
        msg += f" Skipped {skipped} duplicate supervisor_id(s)."
    return True, msg, imported
