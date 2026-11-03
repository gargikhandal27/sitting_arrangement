"""
Independent Verification Engine (Phase 10)

Re-checks a generated seating plan + supervisor allocation against all hard constraints.
Does NOT trust the solver status.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from math import ceil

from services.classroom_layout_service import ClassroomLayout, build_adjacency_list


@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str
    violations: List[str] = field(default_factory=list)


@dataclass
class VerificationReport:
    overall_passed: bool
    checks: List[CheckResult]
    summary: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_passed": self.overall_passed,
            "summary": self.summary,
            "checks": [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "message": c.message,
                    "violations": c.violations,
                }
                for c in self.checks
            ],
        }


def verify_plan(
    seating_assignments: List[Dict[str, Any]],
    supervisor_assignments: Optional[List[Dict[str, Any]]] = None,
    layouts: Optional[List[ClassroomLayout]] = None,
    expected_student_ids: Optional[Set[str]] = None,
    adjacency_mode: str = "horizontal_vertical",
    students_per_supervisor: int = 30,
) -> VerificationReport:
    """
    Run all independent checks.
    """
    checks: List[CheckResult] = []
    supervisor_assignments = supervisor_assignments or []
    layouts = layouts or []

    # ---------- 1. Every required student is assigned exactly once ----------
    student_counts = defaultdict(int)
    for a in seating_assignments:
        student_counts[a["student_id"]] += 1

    dup_students = [sid for sid, cnt in student_counts.items() if cnt > 1]
    missing_students = []
    if expected_student_ids:
        assigned_ids = set(student_counts.keys())
        missing_students = sorted(expected_student_ids - assigned_ids)

    passed = len(dup_students) == 0 and len(missing_students) == 0
    msg = "All students assigned exactly once." if passed else "Student assignment problems found."
    checks.append(CheckResult(
        name="Student uniqueness & completeness",
        passed=passed,
        message=msg,
        violations=(
            [f"Student {s} assigned {student_counts[s]} times" for s in dup_students]
            + [f"Student {s} not assigned" for s in missing_students]
        ),
    ))

    # ---------- 2. No seat has more than one student ----------
    seat_counts = defaultdict(int)
    for a in seating_assignments:
        key = (a["room_id"], a["seat_code"])
        seat_counts[key] += 1
    over_seats = [f"{room}/{code} has {cnt} students" for (room, code), cnt in seat_counts.items() if cnt > 1]
    checks.append(CheckResult(
        name="Seat uniqueness",
        passed=len(over_seats) == 0,
        message="No seat is double-occupied." if not over_seats else "Some seats have multiple students.",
        violations=over_seats,
    ))

    # ---------- 3. Only available seats are used ----------
    available_seats: Set[Tuple[str, str]] = set()
    seat_lookup: Dict[Tuple[str, str], Any] = {}
    for lay in layouts:
        for s in lay.seats:
            if s.is_available:
                available_seats.add((lay.room_id, s.seat_code))
            seat_lookup[(lay.room_id, s.seat_code)] = s

    invalid_seats = []
    for a in seating_assignments:
        key = (a["room_id"], a["seat_code"])
        if key not in available_seats:
            invalid_seats.append(f"{a['room_id']}/{a['seat_code']} is not available or does not exist")
    checks.append(CheckResult(
        name="Seat availability",
        passed=len(invalid_seats) == 0,
        message="All assigned seats are available." if not invalid_seats else "Some assigned seats are unavailable.",
        violations=invalid_seats,
    ))

    # ---------- 4. Batch separation (adjacency) ----------
    # Build map: (room, seat_code) -> batch
    seat_to_batch: Dict[Tuple[str, str], str] = {}
    for a in seating_assignments:
        seat_to_batch[(a["room_id"], a["seat_code"])] = a["batch"]

    adjacency_violations = []
    for lay in layouts:
        adj = build_adjacency_list(lay, mode=adjacency_mode)
        # Map seat_id -> (room, code) and batch
        id_to_key = {s.seat_id: (lay.room_id, s.seat_code) for s in lay.seats}
        for s in lay.seats:
            key = (lay.room_id, s.seat_code)
            if key not in seat_to_batch:
                continue
            my_batch = seat_to_batch[key]
            for neigh_id in adj.get(s.seat_id, []):
                nkey = id_to_key.get(neigh_id)
                if nkey and nkey in seat_to_batch:
                    if seat_to_batch[nkey] == my_batch and key < nkey:  # report each pair once
                        adjacency_violations.append(
                            f"Same batch '{my_batch}' adjacent: {key[0]}/{key[1]} and {nkey[0]}/{nkey[1]}"
                        )

    checks.append(CheckResult(
        name="Batch separation (adjacency)",
        passed=len(adjacency_violations) == 0,
        message="No same-batch students are adjacent." if not adjacency_violations else "Adjacency violations found.",
        violations=adjacency_violations[:50],  # limit display
    ))

    # ---------- 5. Supervisor requirements ----------
    # Skip this check entirely when the caller did not supply any supervisor assignments
    if supervisor_assignments and students_per_supervisor > 0:
        # Count students per room from seating
        room_student_count = defaultdict(int)
        for a in seating_assignments:
            room_student_count[a["room_id"]] += 1

        # Count assigned supervisors per room
        room_sup_count = defaultdict(int)
        for sa in supervisor_assignments:
            room_sup_count[sa["room_id"]] += 1

        # Check uniqueness of supervisors
        sup_ids = [sa["supervisor_id"] for sa in supervisor_assignments]
        dup_sups = [sid for sid in set(sup_ids) if sup_ids.count(sid) > 1]

        sup_violations = []
        for room_id, n_stu in room_student_count.items():
            required = ceil(n_stu / students_per_supervisor)
            assigned = room_sup_count.get(room_id, 0)
            if assigned < required:
                sup_violations.append(
                    f"Room {room_id}: needs {required} supervisor(s), has {assigned}"
                )
        for sid in dup_sups:
            sup_violations.append(f"Supervisor {sid} assigned more than once")

        checks.append(CheckResult(
            name="Supervisor requirements",
            passed=len(sup_violations) == 0,
            message="Supervisor requirements satisfied." if not sup_violations else "Supervisor problems found.",
            violations=sup_violations,
        ))
    else:
        checks.append(CheckResult(
            name="Supervisor requirements",
            passed=True,
            message="Skipped (no supervisor assignments provided or policy disabled).",
            violations=[],
        ))

    # ---------- 6. Basic referential integrity ----------
    ref_violations = []
    for a in seating_assignments:
        if not a.get("student_id") or not a.get("seat_code") or not a.get("room_id"):
            ref_violations.append(f"Incomplete assignment record: {a}")
    checks.append(CheckResult(
        name="Referential integrity",
        passed=len(ref_violations) == 0,
        message="All assignment records are complete." if not ref_violations else "Incomplete records found.",
        violations=ref_violations[:20],
    ))

    # Overall
    overall = all(c.passed for c in checks)
    failed = [c.name for c in checks if not c.passed]
    if overall:
        summary = "ALL CHECKS PASSED. The plan is independently verified."
    else:
        summary = f"VERIFICATION FAILED. Failed checks: {', '.join(failed)}"

    return VerificationReport(overall_passed=overall, checks=checks, summary=summary)
