"""
Supervisor Allocation Module (Phase 9)

Simple, configurable policy:
  required_supervisors = ceil(assigned_students / students_per_supervisor)

Rules:
- Only available supervisors are used
- A supervisor is assigned to at most one classroom per plan
- Occupied classrooms must receive the required number of supervisors
- Shortages are reported clearly
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from math import ceil


@dataclass
class SupervisorInfo:
    supervisor_id: int          # DB pk
    external_id: str
    name: str
    is_available: bool


@dataclass
class RoomDemand:
    room_id: str
    classroom_db_id: int
    num_students: int
    required_supervisors: int


@dataclass
class SupervisorAssignmentResult:
    success: bool
    message: str
    assignments: List[Dict[str, Any]] = field(default_factory=list)  # supervisor -> room
    shortages: List[Dict[str, Any]] = field(default_factory=list)
    total_required: int = 0
    total_assigned: int = 0


def calculate_required_supervisors(num_students: int, students_per_supervisor: int) -> int:
    if students_per_supervisor <= 0:
        return 0
    return ceil(num_students / students_per_supervisor)


def allocate_supervisors(
    room_student_counts: Dict[str, int],          # room_id -> number of students assigned
    room_db_ids: Dict[str, int],                  # room_id -> classroom DB id
    supervisors: List[SupervisorInfo],
    students_per_supervisor: int = 30,
) -> SupervisorAssignmentResult:
    """
    Allocate supervisors to rooms according to the policy.
    """
    if students_per_supervisor <= 0:
        return SupervisorAssignmentResult(
            success=False,
            message="students_per_supervisor must be a positive integer.",
        )

    # Build demands
    demands: List[RoomDemand] = []
    total_required = 0
    for room_id, n_stu in room_student_counts.items():
        if n_stu <= 0:
            continue
        req = calculate_required_supervisors(n_stu, students_per_supervisor)
        total_required += req
        demands.append(RoomDemand(
            room_id=room_id,
            classroom_db_id=room_db_ids.get(room_id, 0),
            num_students=n_stu,
            required_supervisors=req,
        ))

    # Sort rooms by demand (largest first) – simple heuristic
    demands.sort(key=lambda d: d.required_supervisors, reverse=True)

    available = [s for s in supervisors if s.is_available]
    available.sort(key=lambda s: s.external_id)

    assignments = []
    shortages = []
    used_supervisor_ids = set()

    for demand in demands:
        assigned_for_room = 0
        for sup in available:
            if assigned_for_room >= demand.required_supervisors:
                break
            if sup.supervisor_id in used_supervisor_ids:
                continue
            assignments.append({
                "supervisor_db_id": sup.supervisor_id,
                "supervisor_id": sup.external_id,
                "supervisor_name": sup.name,
                "room_id": demand.room_id,
                "classroom_db_id": demand.classroom_db_id,
                "students_in_room": demand.num_students,
            })
            used_supervisor_ids.add(sup.supervisor_id)
            assigned_for_room += 1

        if assigned_for_room < demand.required_supervisors:
            shortages.append({
                "room_id": demand.room_id,
                "required": demand.required_supervisors,
                "assigned": assigned_for_room,
                "shortfall": demand.required_supervisors - assigned_for_room,
            })

    total_assigned = len(assignments)
    success = len(shortages) == 0

    if success:
        msg = f"Successfully assigned {total_assigned} supervisor(s) to {len(demands)} room(s)."
    else:
        msg = (
            f"Assigned {total_assigned} supervisor(s) but there are shortages in "
            f"{len(shortages)} room(s). See details."
        )

    return SupervisorAssignmentResult(
        success=success,
        message=msg,
        assignments=assignments,
        shortages=shortages,
        total_required=total_required,
        total_assigned=total_assigned,
    )
