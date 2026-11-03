"""
Seating Optimization Engine using Google OR-Tools CP-SAT (Phase 8)

Mathematical formulation (simplified):
- Decision variable: x[s, t] = 1 if student s is assigned to seat t
- Constraints:
    1. Each student gets exactly one seat
    2. Each seat gets at most one student
    3. Only available seats are used
    4. Same-batch students are not placed on adjacent seats
- Objective (optional staged):
    - Primary: satisfy all hard constraints
    - Secondary: minimize number of classrooms used
"""
from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
import time
from math import ceil

from ortools.sat.python import cp_model

from services.classroom_layout_service import ClassroomLayout, SeatInfo, build_adjacency_list


@dataclass
class StudentInfo:
    student_id: int          # DB primary key
    external_id: str         # ST001 etc.
    name: str
    batch: str
    roll_number: str


@dataclass
class SolverResult:
    status: str                          # OPTIMAL | FEASIBLE | INFEASIBLE | UNKNOWN | MODEL_INVALID
    status_name: str
    runtime_seconds: float
    assignments: List[Dict[str, Any]] = field(default_factory=list)  # student -> seat
    rooms_used: int = 0
    students_assigned: int = 0
    message: str = ""
    objective_value: Optional[float] = None


def solve_seating(
    students: List[StudentInfo],
    layouts: List[ClassroomLayout],
    adjacency_mode: str = "horizontal_vertical",
    minimize_classrooms: bool = True,
    time_limit_seconds: int = 60,
) -> SolverResult:
    """
    Main solver entry point.
    """
    start = time.time()

    if not students:
        return SolverResult(
            status="MODEL_INVALID",
            status_name="MODEL_INVALID",
            runtime_seconds=0.0,
            message="No students provided.",
        )
    if not layouts:
        return SolverResult(
            status="MODEL_INVALID",
            status_name="MODEL_INVALID",
            runtime_seconds=0.0,
            message="No classroom layouts provided.",
        )

    # Collect all usable seats
    all_seats: List[SeatInfo] = []
    seat_to_room: Dict[int, str] = {}
    for lay in layouts:
        if not lay.is_available:
            continue
        for s in lay.seats:
            if s.is_available:
                all_seats.append(s)
                seat_to_room[s.seat_id] = lay.room_id

    if len(all_seats) < len(students):
        return SolverResult(
            status="INFEASIBLE",
            status_name="INFEASIBLE",
            runtime_seconds=time.time() - start,
            message=f"Not enough seats: {len(all_seats)} usable seats for {len(students)} students.",
        )

    # Build adjacency (seat_id -> list of neighbor seat_ids)
    adjacency: Dict[int, List[int]] = {}
    for lay in layouts:
        adj = build_adjacency_list(lay, mode=adjacency_mode)
        adjacency.update(adj)

    # Group students by batch for separation constraints
    batch_to_students: Dict[str, List[int]] = {}
    for i, stu in enumerate(students):
        batch_to_students.setdefault(stu.batch, []).append(i)

    model = cp_model.CpModel()

    # Decision variables: x[student_idx, seat_idx]
    x = {}
    for i in range(len(students)):
        for j, seat in enumerate(all_seats):
            x[i, j] = model.NewBoolVar(f"x_{i}_{j}")

    # 1. Each student exactly one seat
    for i in range(len(students)):
        model.Add(sum(x[i, j] for j in range(len(all_seats))) == 1)

    # 2. Each seat at most one student
    for j in range(len(all_seats)):
        model.Add(sum(x[i, j] for i in range(len(students))) <= 1)

    # 3. Same-batch students cannot sit on adjacent seats
    seat_id_to_idx = {seat.seat_id: j for j, seat in enumerate(all_seats)}
    for batch, stu_indices in batch_to_students.items():
        if len(stu_indices) < 2:
            continue
        for a in range(len(stu_indices)):
            for b in range(a + 1, len(stu_indices)):
                i1, i2 = stu_indices[a], stu_indices[b]
                for j1, seat1 in enumerate(all_seats):
                    neighbors = adjacency.get(seat1.seat_id, [])
                    for neigh_id in neighbors:
                        j2 = seat_id_to_idx.get(neigh_id)
                        if j2 is not None:
                            # Cannot both be true
                            model.AddBoolOr([x[i1, j1].Not(), x[i2, j2].Not()])

    # 4. Optional: minimize number of classrooms used
    room_ids = sorted(set(seat_to_room.values()))
    room_used = {}
    if minimize_classrooms and room_ids:
        for rid in room_ids:
            room_used[rid] = model.NewBoolVar(f"room_{rid}")
            # If any seat in this room is used, room_used = 1
            seats_in_room = [j for j, seat in enumerate(all_seats) if seat_to_room[seat.seat_id] == rid]
            for j in seats_in_room:
                for i in range(len(students)):
                    model.AddImplication(x[i, j], room_used[rid])
        model.Minimize(sum(room_used[rid] for rid in room_ids))

    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(time_limit_seconds)
    solver.parameters.num_search_workers = 4

    status = solver.Solve(model)
    runtime = time.time() - start

    status_map = {
        cp_model.OPTIMAL: "OPTIMAL",
        cp_model.FEASIBLE: "FEASIBLE",
        cp_model.INFEASIBLE: "INFEASIBLE",
        cp_model.MODEL_INVALID: "MODEL_INVALID",
        cp_model.UNKNOWN: "UNKNOWN",
    }
    status_name = status_map.get(status, "UNKNOWN")

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return SolverResult(
            status=status_name,
            status_name=status_name,
            runtime_seconds=runtime,
            message=f"Solver finished with status {status_name}. No valid assignment found.",
        )

    # Extract assignments
    assignments = []
    rooms_used_set = set()
    for i, stu in enumerate(students):
        for j, seat in enumerate(all_seats):
            if solver.Value(x[i, j]) == 1:
                rid = seat_to_room[seat.seat_id]
                rooms_used_set.add(rid)
                assignments.append({
                    "student_db_id": stu.student_id,
                    "student_id": stu.external_id,
                    "student_name": stu.name,
                    "roll_number": stu.roll_number,
                    "batch": stu.batch,
                    "seat_db_id": seat.seat_id,
                    "seat_code": seat.seat_code,
                    "room_id": rid,
                    "row": seat.row,
                    "column": seat.col,
                })
                break

    return SolverResult(
        status=status_name,
        status_name=status_name,
        runtime_seconds=runtime,
        assignments=assignments,
        rooms_used=len(rooms_used_set),
        students_assigned=len(assignments),
        message=f"Found {status_name} solution. Assigned {len(assignments)} students in {len(rooms_used_set)} room(s).",
        objective_value=solver.ObjectiveValue() if minimize_classrooms else None,
    )
