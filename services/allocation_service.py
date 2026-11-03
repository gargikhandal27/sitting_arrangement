"""
High-level allocation service that connects DB data + NL config to the solvers.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select

from database.models import Student, Classroom, Seat, Supervisor
from services.classroom_layout_service import get_all_layouts, ClassroomLayout
from solvers.seating_solver import solve_seating, StudentInfo, SolverResult
from solvers.supervisor_solver import (
    allocate_supervisors,
    SupervisorInfo,
    SupervisorAssignmentResult,
)


def load_students_for_solver(db: Session) -> List[StudentInfo]:
    rows = db.scalars(select(Student).where(Student.is_active == True).order_by(Student.student_id)).all()
    return [
        StudentInfo(
            student_id=s.id,
            external_id=s.student_id,
            name=s.student_name,
            batch=s.batch,
            roll_number=s.roll_number,
        )
        for s in rows
    ]


def load_supervisors_for_solver(db: Session) -> List[SupervisorInfo]:
    rows = db.scalars(select(Supervisor).order_by(Supervisor.supervisor_id)).all()
    return [
        SupervisorInfo(
            supervisor_id=s.id,
            external_id=s.supervisor_id,
            name=s.supervisor_name,
            is_available=s.is_available,
        )
        for s in rows
    ]


def run_seating_generation(
    db: Session,
    adjacency_mode: str = "horizontal_vertical",
    minimize_classrooms: bool = True,
    time_limit_seconds: int = 60,
) -> Tuple[SolverResult, List[ClassroomLayout]]:
    students = load_students_for_solver(db)
    layouts = get_all_layouts(db)
    # Keep only available classrooms that have seats
    layouts = [lay for lay in layouts if lay.is_available and lay.usable_seats > 0]

    result = solve_seating(
        students=students,
        layouts=layouts,
        adjacency_mode=adjacency_mode,
        minimize_classrooms=minimize_classrooms,
        time_limit_seconds=time_limit_seconds,
    )
    return result, layouts


def run_supervisor_allocation(
    db: Session,
    seating_assignments: List[Dict[str, Any]],
    students_per_supervisor: int = 30,
) -> SupervisorAssignmentResult:
    # Count students per room
    room_counts: Dict[str, int] = {}
    room_db_ids: Dict[str, int] = {}
    for a in seating_assignments:
        rid = a["room_id"]
        room_counts[rid] = room_counts.get(rid, 0) + 1
        # We need classroom DB id – look it up once
        if rid not in room_db_ids:
            classroom = db.scalar(select(Classroom).where(Classroom.room_id == rid))
            room_db_ids[rid] = classroom.id if classroom else 0

    supervisors = load_supervisors_for_solver(db)

    return allocate_supervisors(
        room_student_counts=room_counts,
        room_db_ids=room_db_ids,
        supervisors=supervisors,
        students_per_supervisor=students_per_supervisor,
    )
