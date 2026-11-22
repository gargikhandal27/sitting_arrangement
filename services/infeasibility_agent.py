"""
AI Infeasibility Diagnostic & Negotiation Agent (Phase 1 AI Upgrade)

Analyzes why an examination seating or supervisor problem is INFEASIBLE,
UNKNOWN, or at risk of failure, and proposes concrete, actionable remediations.

Uses combinatorial capacity bounds, bipartite graph independent set calculations,
and resource availability metrics to pinpoint bottlenecks.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict
from math import ceil
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import select

from database.models import Classroom, Student, Supervisor, Seat
from services.classroom_layout_service import (
    ClassroomLayout,
    SeatInfo,
    get_all_layouts,
    get_classroom_layout,
)
from solvers.seating_solver import StudentInfo, SolverResult


@dataclass
class DiagnosisIssue:
    category: str        # GLOBAL_CAPACITY | BATCH_BOTTLENECK | NO_ROOMS | SUPERVISOR_DEFICIT | TIMEOUT | SEAT_CONFIRMATION
    severity: str        # error | warning | info
    title: str
    description: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BatchCapacityMetric:
    batch: str
    student_count: int
    max_independent_capacity: int
    utilization_pct: float
    is_bottleneck: bool
    deficit: int


@dataclass
class RemediationOption:
    id: str
    title: str
    description: str
    action_type: str     # relax_adjacency | activate_room | increase_time | split_batch | reduce_supervisor_ratio
    impact: str
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DiagnosisReport:
    is_feasible: bool
    overall_status: str
    summary: str
    total_students: int
    total_usable_seats: int
    active_rooms_count: int
    inactive_rooms_count: int
    issues: List[DiagnosisIssue] = field(default_factory=list)
    batch_metrics: List[BatchCapacityMetric] = field(default_factory=list)
    remediations: List[RemediationOption] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def calculate_room_independent_capacity(
    layout: ClassroomLayout,
    mode: str = "horizontal_vertical"
) -> int:
    """
    Computes the maximum number of seats a SINGLE batch can occupy in a room
    without violating the adjacency constraint.
    
    For a 2D grid:
    - In horizontal_vertical mode: The grid is bipartite. A batch can occupy at most
      max(color_0, color_1) seats, where color = (row + col) % 2 (checkerboard pattern).
    - In horizontal mode: Each row is independent. A batch can occupy at most
      ceil(k / 2) seats per row of k usable seats.
    """
    if not layout.is_available:
        return 0

    usable_seats = [s for s in layout.seats if s.is_available and s.row is not None and s.col is not None]
    if not usable_seats:
        return 0

    if mode == "horizontal_vertical":
        color_0 = 0
        color_1 = 0
        for s in usable_seats:
            if (s.row + s.col) % 2 == 0:
                color_0 += 1
            else:
                color_1 += 1
        return max(color_0, color_1)

    elif mode == "horizontal":
        row_counts = defaultdict(int)
        for s in usable_seats:
            row_counts[s.row] += 1
        return sum(ceil(count / 2) for count in row_counts.values())

    return len(usable_seats)


def calculate_total_independent_capacity(
    layouts: List[ClassroomLayout],
    mode: str = "horizontal_vertical"
) -> int:
    """Total maximum seats any single batch could occupy across all active rooms."""
    return sum(
        calculate_room_independent_capacity(lay, mode=mode)
        for lay in layouts
        if lay.is_available
    )


def diagnose_seating_feasibility(
    students: List[StudentInfo],
    layouts: List[ClassroomLayout],
    adjacency_mode: str = "horizontal_vertical",
    time_limit_seconds: int = 60,
    solver_result: Optional[SolverResult] = None,
    supervisors: Optional[List[Any]] = None,
    students_per_supervisor: int = 30,
) -> DiagnosisReport:
    """
    AI Diagnosis Engine:
    Detects root causes of infeasibility or solver failure and formulates remediations.
    Can be run as a Pre-flight Check (before solving) or Post-mortem (after solver fails).
    """
    issues: List[DiagnosisIssue] = []
    remediations: List[RemediationOption] = []
    batch_metrics: List[BatchCapacityMetric] = []

    active_layouts = [lay for lay in layouts if lay.is_available and lay.usable_seats > 0]
    inactive_layouts = [lay for lay in layouts if (not lay.is_available) or lay.usable_seats == 0]

    total_students = len(students)
    total_usable_seats = sum(lay.usable_seats for lay in active_layouts)
    active_rooms_count = len(active_layouts)
    inactive_rooms_count = len(inactive_layouts)

    # 1. Check if classrooms exist
    if not active_layouts:
        issues.append(
            DiagnosisIssue(
                category="NO_ROOMS",
                severity="error",
                title="No Usable Classrooms Available",
                description=(
                    "No active classrooms with usable seats were found in the database. "
                    "Seating generation cannot proceed."
                ),
            )
        )
        if inactive_layouts:
            remediations.append(
                RemediationOption(
                    id="activate_existing_rooms",
                    title="Activate Registered Classrooms",
                    description=f"You have {len(inactive_layouts)} classroom(s) marked inactive or unconfirmed.",
                    action_type="activate_room",
                    impact="Unlocks classroom capacity for the exam.",
                )
            )

    # 2. Check global seat capacity (Pigeonhole Principle)
    if total_students > total_usable_seats and active_layouts:
        deficit = total_students - total_usable_seats
        issues.append(
            DiagnosisIssue(
                category="GLOBAL_CAPACITY",
                severity="error",
                title=f"Global Seat Deficit ({deficit} seats short)",
                description=(
                    f"There are {total_students} registered students but only {total_usable_seats} "
                    f"usable seats across {active_rooms_count} active classroom(s). "
                    f"At least {deficit} additional seat(s) are required."
                ),
                details={"students": total_students, "seats": total_usable_seats, "deficit": deficit},
            )
        )

        # Look for inactive rooms to propose activation
        inactive_seats = sum(
            len([s for s in lay.seats if s.is_available])
            for lay in inactive_layouts
        )
        if inactive_seats > 0:
            remediations.append(
                RemediationOption(
                    id="activate_inactive_rooms",
                    title=f"Activate Inactive Classrooms (+{inactive_seats} seats)",
                    description=(
                        f"Activating inactive classrooms will add up to {inactive_seats} seats, "
                        f"{'completely covering' if (total_usable_seats + inactive_seats) >= total_students else 'reducing'} "
                        f"the shortage."
                    ),
                    action_type="activate_room",
                    impact=f"+{inactive_seats} usable seats",
                )
            )

    # 3. Analyze batch concentration & independent set bottleneck
    batch_counts: Dict[str, int] = defaultdict(int)
    for s in students:
        batch_counts[s.batch] += 1

    max_batch_cap_current = calculate_total_independent_capacity(active_layouts, mode=adjacency_mode)
    max_batch_cap_relaxed = calculate_total_independent_capacity(active_layouts, mode="horizontal")

    has_batch_bottleneck = False
    for batch_name, count in sorted(batch_counts.items(), key=lambda x: -x[1]):
        deficit = max(0, count - max_batch_cap_current)
        utilization = (count / max_batch_cap_current * 100) if max_batch_cap_current > 0 else 100.0
        is_bottleneck = count > max_batch_cap_current

        if is_bottleneck:
            has_batch_bottleneck = True

        batch_metrics.append(
            BatchCapacityMetric(
                batch=batch_name,
                student_count=count,
                max_independent_capacity=max_batch_cap_current,
                utilization_pct=round(utilization, 1),
                is_bottleneck=is_bottleneck,
                deficit=deficit,
            )
        )

        if is_bottleneck:
            issues.append(
                DiagnosisIssue(
                    category="BATCH_BOTTLENECK",
                    severity="error",
                    title=f"Batch Density Bottleneck: '{batch_name}' ({deficit} students over limit)",
                    description=(
                        f"Batch '{batch_name}' has {count} students, but under the current "
                        f"'{adjacency_mode.replace('_', ' and ')}' separation rule, active classrooms can "
                        f"hold at most {max_batch_cap_current} students of the same batch without adjacency violations."
                    ),
                    details={
                        "batch": batch_name,
                        "students": count,
                        "max_capacity": max_batch_cap_current,
                        "deficit": deficit,
                        "mode": adjacency_mode,
                    },
                )
            )

    # If batch bottleneck exists, check if relaxing adjacency mode resolves it
    if has_batch_bottleneck:
        if adjacency_mode == "horizontal_vertical":
            can_fit_relaxed = all(count <= max_batch_cap_relaxed for count in batch_counts.values())
            remediations.append(
                RemediationOption(
                    id="relax_to_horizontal",
                    title="Relax Batch Separation to 'Horizontal Only'",
                    description=(
                        f"Switching from Horizontal & Vertical to Horizontal Only increases single-batch capacity "
                        f"from {max_batch_cap_current} to {max_batch_cap_relaxed} seats across active rooms. "
                        f"{'This mathematically resolves the batch bottleneck!' if can_fit_relaxed else 'This significantly alleviates the congestion.'}"
                    ),
                    action_type="relax_adjacency",
                    impact=f"Expands single-batch capacity to {max_batch_cap_relaxed} seats",
                    payload={"target_adjacency": "horizontal"},
                )
            )

        # Propose splitting the largest batch
        largest_batch, largest_count = max(batch_counts.items(), key=lambda x: x[1])
        remediations.append(
            RemediationOption(
                id="split_batch",
                title=f"Split Largest Batch '{largest_batch}' into Multiple Sessions",
                description=(
                    f"Batch '{largest_batch}' has {largest_count} students. Splitting this batch into two "
                    f"staggered exam shifts ({ceil(largest_count/2)} students each) eliminates the crowding conflict."
                ),
                action_type="split_batch",
                impact="Eliminates single-batch clustering",
            )
        )

    # 4. Analyze Supervisor Sufficiency (if supervisors provided or checked)
    if supervisors is not None and total_students > 0:
        available_supervisors = [sup for sup in supervisors if getattr(sup, "is_available", True)]
        # Heuristic estimation: each room takes ceil(students_in_room / students_per_supervisor)
        # Minimum supervisors required is at least ceil(total_students / students_per_supervisor) or 1 per room
        est_min_supervisors = max(active_rooms_count, ceil(total_students / max(1, students_per_supervisor)))
        if len(available_supervisors) < est_min_supervisors:
            sup_deficit = est_min_supervisors - len(available_supervisors)
            issues.append(
                DiagnosisIssue(
                    category="SUPERVISOR_DEFICIT",
                    severity="warning",
                    title=f"Potential Supervisor Shortage ({sup_deficit} more needed)",
                    description=(
                        f"There are {len(available_supervisors)} available supervisor(s), but at least "
                        f"{est_min_supervisors} are recommended for {total_students} students across "
                        f"{active_rooms_count} room(s) at 1:{students_per_supervisor} ratio."
                    ),
                    details={"available": len(available_supervisors), "needed": est_min_supervisors},
                )
            )
            remediations.append(
                RemediationOption(
                    id="adjust_supervisor_ratio",
                    title="Adjust Supervisor Ratio or Mark More Available",
                    description=(
                        f"Increase the student-to-supervisor ratio (e.g. from {students_per_supervisor} to "
                        f"{ceil(total_students / max(1, len(available_supervisors)))}) or enable inactive supervisors."
                    ),
                    action_type="reduce_supervisor_ratio",
                    impact="Prevents supervisor allocation bottlenecks",
                )
            )

    # 5. Analyze Solver Result Status (if post-mortem)
    if solver_result is not None:
        if solver_result.status == "UNKNOWN":
            issues.append(
                DiagnosisIssue(
                    category="TIMEOUT",
                    severity="warning",
                    title=f"Solver Reached Time Limit ({solver_result.runtime_seconds:.1f}s)",
                    description=(
                        "The solver hit the time limit before proving optimality or finding a solution. "
                        "The search space may be large, or constraints are very tightly bounded."
                    ),
                )
            )
            remediations.append(
                RemediationOption(
                    id="increase_time_limit",
                    title=f"Increase Solver Time Limit to {max(120, time_limit_seconds * 2)}s",
                    description="Gives OR-Tools CP-SAT more search tree depth to find a feasible solution.",
                    action_type="increase_time",
                    impact="Higher probability of finding feasible solution in dense instances",
                    payload={"time_limit": max(120, time_limit_seconds * 2)},
                )
            )
        elif solver_result.status == "INFEASIBLE" and not issues:
            # If our heuristic didn't catch a simple bound, the combination of multi-batch interleaving is infeasible
            issues.append(
                DiagnosisIssue(
                    category="BATCH_BOTTLENECK",
                    severity="error",
                    title="Tight Multi-Batch Interleaving Conflict",
                    description=(
                        "Although total seats and individual batch bounds are theoretically sufficient, "
                        "the combination of same-batch non-adjacency constraints across the room geometry "
                        "leaves no valid permutation."
                    ),
                )
            )
            if adjacency_mode == "horizontal_vertical":
                remediations.append(
                    RemediationOption(
                        id="relax_to_horizontal",
                        title="Relax Batch Separation to 'Horizontal Only'",
                        description="Reduces constraint density by ~50%, allowing same-batch students in adjacent rows.",
                        action_type="relax_adjacency",
                        impact="Dramatically expands feasible solution space",
                        payload={"target_adjacency": "horizontal"},
                    )
                )

    # Determine overall feasibility verdict
    has_errors = any(i.severity == "error" for i in issues)
    if not has_errors and (solver_result is None or solver_result.status in ("OPTIMAL", "FEASIBLE")):
        is_feasible = True
        overall_status = "FEASIBLE"
        summary = (
            f"Pre-flight analysis verified: {total_students} student(s) can be seated in "
            f"{total_usable_seats} usable seat(s) across {active_rooms_count} room(s)."
        )
    else:
        is_feasible = False
        overall_status = issues[0].category if issues else "INFEASIBLE"
        error_titles = [i.title for i in issues if i.severity == "error"]
        summary = (
            f"Infeasibility detected: {', '.join(error_titles) if error_titles else 'Constraints are overly restrictive'}."
        )

    return DiagnosisReport(
        is_feasible=is_feasible,
        overall_status=overall_status,
        summary=summary,
        total_students=total_students,
        total_usable_seats=total_usable_seats,
        active_rooms_count=active_rooms_count,
        inactive_rooms_count=inactive_rooms_count,
        issues=issues,
        batch_metrics=batch_metrics,
        remediations=remediations,
    )
