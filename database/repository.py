"""
Basic repository helpers for common database operations.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from database.models import (
    Student, Classroom, Seat, Supervisor,
    ExaminationSession, SeatingPlan
)


def count_students(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Student)) or 0


def count_classrooms(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Classroom)) or 0


def count_available_seats(db: Session) -> int:
    return db.scalar(
        select(func.count()).select_from(Seat).where(Seat.is_available == True)
    ) or 0


def count_supervisors(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Supervisor)) or 0


def count_plans(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(SeatingPlan)) or 0


def get_all_students(db: Session) -> List[Student]:
    return list(db.scalars(select(Student).order_by(Student.student_id)).all())


def get_students_records_fast(db: Session, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Fast columnar fetch avoiding full ORM instance hydration."""
    query = select(Student.student_id, Student.roll_number, Student.student_name, Student.batch).order_by(Student.student_id)
    if limit:
        query = query.limit(limit)
    rows = db.execute(query).all()
    return [
        {
            "student_id": r[0],
            "roll_number": r[1],
            "student_name": r[2],
            "batch": r[3],
        }
        for r in rows
    ]


def get_student_by_student_id(db: Session, student_id: str) -> Optional[Student]:
    return db.scalar(select(Student).where(Student.student_id == student_id))


def get_all_classrooms(db: Session) -> List[Classroom]:
    return list(db.scalars(select(Classroom).order_by(Classroom.room_id)).all())


def get_classroom_by_room_id(db: Session, room_id: str) -> Optional[Classroom]:
    return db.scalar(select(Classroom).where(Classroom.room_id == room_id))


def get_all_supervisors(db: Session) -> List[Supervisor]:
    return list(db.scalars(select(Supervisor).order_by(Supervisor.supervisor_id)).all())
