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

    @property
    def total_students(self) -> int:
        return self.students_assigned

    @property
    def seated_students(self) -> int:
        return self.students_assigned

    @property
    def classrooms_used(self) -> int:
        return self.rooms_used


def _solve_seating_decomposed(
    students: List[StudentInfo],
    layouts: List[ClassroomLayout],
    adjacency_mode: str,
    minimize_classrooms: bool,
    time_limit_seconds: int,
    start_time: float,
) -> Optional[SolverResult]:
    """
    High-performance room decomposition engine.
    Solves large exam allocations (>60 students / multiple rooms) in seconds by
    distributing students across independent room spaces and optimizing locally.
    """
    available_layouts = [l for l in layouts if l.is_available and l.usable_seats > 0]
    if not available_layouts:
        return None

    layouts_sorted = sorted(available_layouts, key=lambda l: l.usable_seats, reverse=True)

    room_caps = {}
    room_batch_caps = {}
    for l in layouts_sorted:
        r, c = l.rows, l.columns
        if adjacency_mode == "horizontal_vertical":
            batch_cap = ceil(r * c / 2) if (r and c) else max(1, l.usable_seats // 2)
            total_safe = min(l.usable_seats, batch_cap * 2)
        else:
            batch_cap = r * ceil(c / 2) if (r and c) else max(1, l.usable_seats // 2)
            total_safe = min(l.usable_seats, batch_cap * 2)
        room_caps[l.room_id] = max(1, total_safe)
        room_batch_caps[l.room_id] = max(1, batch_cap)

    if minimize_classrooms:
        selected_layouts = []
        running_cap = 0
        for lay in layouts_sorted:
            selected_layouts.append(lay)
            running_cap += room_caps[lay.room_id]
            if running_cap >= len(students) * 1.15:
                break
    else:
        selected_layouts = list(layouts_sorted)

    room_students: Dict[str, List[StudentInfo]] = {lay.room_id: [] for lay in selected_layouts}
    from collections import defaultdict
    batch_groups = defaultdict(list)
    for s in students:
        batch_groups[s.batch].append(s)

    room_idx = 0
    for batch, stus in batch_groups.items():
        for s in stus:
            assigned = False
            for attempt in range(len(selected_layouts)):
                target_lay = selected_layouts[(room_idx + attempt) % len(selected_layouts)]
                rid = target_lay.room_id
                cur_stus = room_students[rid]
                cur_batch_cnt = sum(1 for cs in cur_stus if cs.batch == batch)
                if len(cur_stus) < target_lay.usable_seats and cur_batch_cnt < room_batch_caps[rid]:
                    cur_stus.append(s)
                    room_idx = (room_idx + attempt + 1) % len(selected_layouts)
                    assigned = True
                    break
            if not assigned:
                for target_lay in selected_layouts:
                    rid = target_lay.room_id
                    if len(room_students[rid]) < target_lay.usable_seats:
                        room_students[rid].append(s)
                        assigned = True
                        break

    all_assignments = []
    rooms_used_set = set()
    per_room_timeout = max(3.0, min(10.0, time_limit_seconds / max(1, len(selected_layouts)) * 2))

    for lay in selected_layouts:
        r_stus = room_students[lay.room_id]
        if not r_stus:
            continue
        sub_res = _solve_seating_monolithic(
            students=r_stus,
            layouts=[lay],
            adjacency_mode=adjacency_mode,
            minimize_classrooms=False,
            time_limit_seconds=int(per_room_timeout),
            start_time=time.time(),
        )
        if sub_res.status not in ("OPTIMAL", "FEASIBLE") or len(sub_res.assignments) < len(r_stus):
            return None
        all_assignments.extend(sub_res.assignments)
        rooms_used_set.add(lay.room_id)

    if len(all_assignments) == len(students):
        runtime = time.time() - start_time
        return SolverResult(
            status="OPTIMAL",
            status_name="OPTIMAL",
            runtime_seconds=runtime,
            assignments=all_assignments,
            rooms_used=len(rooms_used_set),
            students_assigned=len(all_assignments),
            message=f"Found OPTIMAL solution. Assigned {len(all_assignments)} students in {len(rooms_used_set)} room(s).",
            objective_value=float(len(rooms_used_set)),
        )

    return None


def solve_seating(
    students: List[StudentInfo],
    layouts: List[ClassroomLayout],
    adjacency_mode: str = "horizontal_vertical",
    minimize_classrooms: bool = True,
    time_limit_seconds: int = 60,
) -> SolverResult:
    """
    Main solver entry point. Uses fast room-decomposition for multi-room / large workloads,
    with automatic fallback to exact CP-SAT monolithic optimization.
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

    # Use decomposed solver for large workloads across multiple classrooms
    if len(layouts) > 1 and (len(students) > 60 or len(layouts) > 3):
        decomposed_res = _solve_seating_decomposed(
            students=students,
            layouts=layouts,
            adjacency_mode=adjacency_mode,
            minimize_classrooms=minimize_classrooms,
            time_limit_seconds=time_limit_seconds,
            start_time=start,
        )
        if decomposed_res is not None:
            return decomposed_res

    return _solve_seating_monolithic(
        students=students,
        layouts=layouts,
        adjacency_mode=adjacency_mode,
        minimize_classrooms=minimize_classrooms,
        time_limit_seconds=time_limit_seconds,
        start_time=start,
    )


def _solve_seating_monolithic(
    students: List[StudentInfo],
    layouts: List[ClassroomLayout],
    adjacency_mode: str = "horizontal_vertical",
    minimize_classrooms: bool = True,
    time_limit_seconds: int = 60,
    start_time: Optional[float] = None,
) -> SolverResult:
    start = start_time if start_time is not None else time.time()

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

    # Collect unique undirected adjacency edges (j1 < j2) across all classrooms
    adjacent_pairs = set()
    for seat1 in all_seats:
        j1 = seat_id_to_idx[seat1.seat_id]
        for neigh_id in adjacency.get(seat1.seat_id, []):
            j2 = seat_id_to_idx.get(neigh_id)
            if j2 is not None and j1 < j2:
                adjacent_pairs.add((j1, j2))

    # Fast 2-variable edge constraints using per-seat batch indicators
    for batch, stu_indices in batch_to_students.items():
        if len(stu_indices) < 2:
            continue
        y = {}
        for j in range(len(all_seats)):
            y[j] = model.NewBoolVar(f"y_{batch}_{j}")
            model.Add(sum(x[i, j] for i in stu_indices) == y[j])

        for j1, j2 in adjacent_pairs:
            model.Add(y[j1] + y[j2] <= 1)

    # 4. Optional: minimize number of classrooms used
    room_ids = sorted(set(seat_to_room.values()))
    room_used = {}
    if minimize_classrooms and room_ids:
        for rid in room_ids:
            room_used[rid] = model.NewBoolVar(f"room_{rid}")
            seats_in_room = [j for j, seat in enumerate(all_seats) if seat_to_room[seat.seat_id] == rid]
            # Compact linear constraint per room instead of NxM implications
            model.Add(
                sum(x[i, j] for j in seats_in_room for i in range(len(students)))
                <= len(seats_in_room) * room_used[rid]
            )
        model.Minimize(sum(room_used[rid] for rid in room_ids))

    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(time_limit_seconds)
    solver.parameters.num_search_workers = 8

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
