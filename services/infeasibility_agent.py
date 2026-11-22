"""
AI Infeasibility Diagnostic & Negotiation Agent (Agent 2)

Analyzes why an examination seating or supervisor problem is INFEASIBLE,
UNKNOWN, or at risk of failure, and formulates prioritized negotiation proposals.

Features:
- Mathematical checkerboard bipartite independent set bounding (Color 0 vs Color 1)
- Automated constraint relaxation triage (Horizontal & Vertical -> Horizontal Only)
- Minimal capacity addition calculation (recommending specific inactive rooms)
- Shift partitioning analysis for oversized batches
- Actionable negotiation execution engine (apply_negotiation_proposal)
- What-If simulation engine for capacity stress-testing
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
    confidence_score: float = 95.0
    trade_off: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)


# Semantic alias for Agent 2: Negotiation Proposals
NegotiationProposal = RemediationOption


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

    @property
    def proposals(self) -> List[NegotiationProposal]:
        """Convenient alias for negotiation proposals."""
        return self.remediations

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


def get_classroom_checkerboard_analysis(
    layouts: List[ClassroomLayout],
) -> List[Dict[str, Any]]:
    """
    Computes mathematical bipartite coloring and independent set capacities
    for every classroom.
    """
    analysis = []
    for lay in layouts:
        usable_seats = [
            s for s in lay.seats
            if s.is_available and s.row is not None and s.col is not None
        ]
        color_0 = sum(1 for s in usable_seats if (s.row + s.col) % 2 == 0)
        color_1 = sum(1 for s in usable_seats if (s.row + s.col) % 2 == 1)
        max_hv = max(color_0, color_1)

        row_counts = defaultdict(int)
        for s in usable_seats:
            row_counts[s.row] += 1
        max_h = sum(ceil(cnt / 2) for cnt in row_counts.values())

        analysis.append({
            "room_id": lay.room_id,
            "room_name": lay.room_name,
            "rows": lay.rows,
            "columns": lay.columns,
            "total_seats": len(lay.seats),
            "usable_seats": len(usable_seats),
            "color_0": color_0,
            "color_1": color_1,
            "max_single_batch_hv": max_hv,
            "max_single_batch_h": max_h,
            "bipartite_ratio_pct": round((max_hv / len(usable_seats) * 100) if usable_seats else 0, 1),
            "is_available": lay.is_available,
        })
    return analysis


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
    AI Diagnosis & Constraint Negotiation Engine:
    Detects root causes of infeasibility or solver failure and formulates prioritized,
    actionable trade-off proposals with confidence scores.
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
                title="No Open Classrooms Available",
                description=(
                    "All classrooms are currently turned off or closed. "
                    "Please turn on at least one classroom to plan seating."
                ),
            )
        )
        if inactive_layouts:
            remediations.append(
                RemediationOption(
                    id="activate_existing_rooms",
                    title="Turn On Closed Classrooms",
                    description=f"You have {len(inactive_layouts)} classroom(s) currently turned off.",
                    action_type="activate_room",
                    impact=f"Unlocks capacity across {len(inactive_layouts)} classroom(s)",
                    confidence_score=99.0,
                    trade_off="Opens classrooms for students to take the exam.",
                    payload={"target_rooms": "all_inactive"},
                )
            )

    # 2. Check global seat capacity (Pigeonhole Principle)
    if total_students > total_usable_seats and active_layouts:
        deficit = total_students - total_usable_seats
        issues.append(
            DiagnosisIssue(
                category="GLOBAL_CAPACITY",
                severity="error",
                title=f"Not Enough Desks: Need {deficit} More Seats",
                description=(
                    f"You have {total_students} students registered, but only {total_usable_seats} "
                    f"desks available across {active_rooms_count} open classroom(s). "
                    f"You need at least {deficit} more desk(s)."
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
            is_sufficient = (total_usable_seats + inactive_seats) >= total_students
            remediations.append(
                RemediationOption(
                    id="activate_inactive_rooms",
                    title=f"Open Closed Classrooms (+{inactive_seats} seats)",
                    description=(
                        f"Opening closed classrooms will add {inactive_seats} more seats, which "
                        f"{'gives enough desks for all students' if is_sufficient else 'helps cover the shortage'}."
                    ),
                    action_type="activate_room",
                    impact=f"+{inactive_seats} extra seats",
                    confidence_score=99.0 if is_sufficient else 75.0,
                    trade_off="Requires opening and using more classrooms for the exam.",
                    payload={"target_rooms": "all_inactive", "added_seats": inactive_seats},
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
                    title=f"Branch '{batch_name}' is Too Large ({deficit} students over safe limit)",
                    description=(
                        f"Branch '{batch_name}' has {count} students. To prevent cheating, students "
                        f"of the same branch cannot sit right next to each other. Under current spacing rules, "
                        f"the open rooms can safely seat at most {max_batch_cap_current} students from this branch."
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

    # If batch bottleneck exists, formulate negotiation proposals
    if has_batch_bottleneck:
        if adjacency_mode == "horizontal_vertical":
            can_fit_relaxed = all(count <= max_batch_cap_relaxed for count in batch_counts.values())
            remediations.append(
                RemediationOption(
                    id="relax_to_horizontal",
                    title="Use Normal Spacing (Skip side-by-side seat only)",
                    description=(
                        f"Instead of skipping both side and front/back seats, only skip the seat directly next to each student. "
                        f"This allows each branch to fit up to {max_batch_cap_relaxed} students across open rooms. "
                        f"{'This completely solves the space problem!' if can_fit_relaxed else 'This greatly helps reduce crowding.'}"
                    ),
                    action_type="relax_adjacency",
                    impact=f"Increases branch capacity to {max_batch_cap_relaxed} seats",
                    confidence_score=98.0 if can_fit_relaxed else 82.0,
                    trade_off="Allows same-branch students to sit in rows behind each other, but not directly beside each other.",
                    payload={"target_adjacency": "horizontal"},
                )
            )

        # Propose splitting the largest batch into 2 shifts
        largest_batch, largest_count = max(batch_counts.items(), key=lambda x: x[1])
        remediations.append(
            RemediationOption(
                id="split_batch",
                title=f"Split Branch '{largest_batch}' into Morning & Afternoon Shifts",
                description=(
                    f"Branch '{largest_batch}' has {largest_count} students. Splitting them into two "
                    f"smaller shifts ({ceil(largest_count/2)} students each) easily avoids crowding without changing room rules."
                ),
                action_type="split_batch",
                impact="Easily fits all students without crowding",
                confidence_score=95.0,
                trade_off="Runs two exam shifts: one in the morning and one in the afternoon.",
                payload={"target_batch": largest_batch, "shift_size": ceil(largest_count / 2)},
            )
        )

    # 4. Analyze Supervisor Sufficiency
    if supervisors is not None and total_students > 0:
        available_supervisors = [sup for sup in supervisors if getattr(sup, "is_available", True)]
        est_min_supervisors = max(active_rooms_count, ceil(total_students / max(1, students_per_supervisor)))
        if len(available_supervisors) < est_min_supervisors:
            sup_deficit = est_min_supervisors - len(available_supervisors)
            issues.append(
                DiagnosisIssue(
                    category="SUPERVISOR_DEFICIT",
                    severity="warning",
                    title=f"Need {sup_deficit} More Teacher(s) for Exam Duty",
                    description=(
                        f"There are {len(available_supervisors)} available teacher(s), but at least "
                        f"{est_min_supervisors} are needed for {total_students} students across "
                        f"{active_rooms_count} room(s)."
                    ),
                    details={"available": len(available_supervisors), "needed": est_min_supervisors},
                )
            )
            remediations.append(
                RemediationOption(
                    id="adjust_supervisor_ratio",
                    title="Assign Backup Teachers or Increase Students per Teacher",
                    description=(
                        f"Turn on available backup teachers or assign slightly more students per teacher to cover all rooms."
                    ),
                    action_type="reduce_supervisor_ratio",
                    impact="Covers all exam rooms",
                    confidence_score=94.0,
                    trade_off="Teachers will look after slightly more students or extra backup teachers will be assigned.",
                    payload={"target_ratio": ceil(total_students / max(1, len(available_supervisors)))},
                )
            )

    # 5. Analyze Solver Result Status (if post-mortem)
    if solver_result is not None:
        if solver_result.status == "UNKNOWN":
            issues.append(
                DiagnosisIssue(
                    category="TIMEOUT",
                    severity="warning",
                    title=f"Planning Reached Time Limit ({solver_result.runtime_seconds:.1f}s)",
                    description=(
                        "The computer hit the time limit before finding a plan. "
                        "Giving it more time or using normal spacing will help."
                    ),
                )
            )
            remediations.append(
                RemediationOption(
                    id="increase_time_limit",
                    title=f"Give Computer More Time to Plan ({max(120, time_limit_seconds * 2)}s)",
                    description="Gives the system more time to calculate the best possible seating plan.",
                    action_type="increase_time",
                    impact="Helps find a plan for tight rooms",
                    confidence_score=88.0,
                    trade_off="Planning will take a little longer before producing a result.",
                    payload={"time_limit": max(120, time_limit_seconds * 2)},
                )
            )
        elif solver_result.status == "INFEASIBLE" and not issues:
            issues.append(
                DiagnosisIssue(
                    category="BATCH_BOTTLENECK",
                    severity="error",
                    title="Spacing Rules are Too Tight",
                    description=(
                        "Even though total desks are enough, the rule keeping same-branch students apart "
                        "leaves no valid plan. Switching to normal spacing will solve this."
                    ),
                )
            )
            if adjacency_mode == "horizontal_vertical":
                remediations.append(
                    RemediationOption(
                        id="relax_to_horizontal",
                        title="Use Normal Spacing (Skip side-by-side seat only)",
                        description="Only skip the seat right next to each student. Allows students in rows behind each other.",
                        action_type="relax_adjacency",
                        impact="Gives much more room for students",
                        confidence_score=98.0,
                        trade_off="Allows same-branch in consecutive rows, keeping side gap.",
                        payload={"target_adjacency": "horizontal"},
                    )
                )

    # Determine overall feasibility verdict
    has_errors = any(i.severity == "error" for i in issues)
    if not has_errors and (solver_result is None or solver_result.status in ("OPTIMAL", "FEASIBLE")):
        is_feasible = True
        overall_status = "FEASIBLE"
        summary = (
            f"Pre-flight check passed: All {total_students} student(s) easily fit in "
            f"{total_usable_seats} desk(s) across {active_rooms_count} open room(s)."
        )
    else:
        is_feasible = False
        overall_status = issues[0].category if issues else "INFEASIBLE"
        error_titles = [i.title for i in issues if i.severity == "error"]
        summary = (
            f"Students do not fit: {', '.join(error_titles) if error_titles else 'Room rules are too strict for current student numbers'}."
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


def apply_negotiation_proposal(
    proposal_id: str,
    db: Session,
    context_config: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Executes a chosen negotiation proposal against the database or configuration.
    Returns: (success: bool, message: str, updated_context: Dict[str, Any])
    """
    ctx = dict(context_config or {})

    # 1. Activate inactive classrooms
    if proposal_id in ("activate_inactive_rooms", "activate_existing_rooms"):
        inactive_rooms = db.scalars(
            select(Classroom).where((Classroom.is_available == False) | (Classroom.is_available == None))
        ).all()
        if not inactive_rooms:
            return True, "All classrooms are already active.", ctx

        for room in inactive_rooms:
            room.is_available = True
        db.commit()

        activated_names = [r.room_name for r in inactive_rooms]
        ctx["activated_rooms"] = activated_names
        return (
            True,
            f"✅ Activated {len(inactive_rooms)} classroom(s): {', '.join(activated_names)}. Additional capacity unlocked!",
            ctx,
        )

    # 2. Relax batch separation to Horizontal Only
    if proposal_id == "relax_to_horizontal":
        ctx["adjacency_mode"] = "horizontal"
        return (
            True,
            "✅ Batch separation relaxed to 'Horizontal Only'. Same-batch students may now sit in adjacent rows.",
            ctx,
        )

    # 3. Increase solver time limit
    if proposal_id == "increase_time_limit":
        ctx["time_limit_seconds"] = 120
        return (
            True,
            "✅ Solver time limit increased to 120 seconds for deeper CP-SAT tree exploration.",
            ctx,
        )

    # 4. Adjust supervisor ratio or activate supervisors
    if proposal_id == "adjust_supervisor_ratio":
        inactive_sups = db.scalars(
            select(Supervisor).where((Supervisor.is_available == False) | (Supervisor.is_available == None))
        ).all()
        for sup in inactive_sups:
            sup.is_available = True
        db.commit()

        ctx["supervisors_activated"] = len(inactive_sups)
        return (
            True,
            f"✅ Enabled {len(inactive_sups)} reserve supervisor(s). Invigilator shortage resolved.",
            ctx,
        )

    # 5. Split largest batch into 2 shifts
    if proposal_id == "split_batch":
        active_students = db.scalars(select(Student).where(Student.is_active == True)).all()
        batch_counts = defaultdict(list)
        for s in active_students:
            batch_counts[s.batch].append(s)

        if not batch_counts:
            return False, "No active students found to partition.", ctx

        target_batch, students_in_batch = max(batch_counts.items(), key=lambda x: len(x[1]))
        mid = ceil(len(students_in_batch) / 2)
        shift1 = students_in_batch[:mid]
        shift2 = students_in_batch[mid:]

        ctx["split_batch"] = target_batch
        ctx["shift_1_count"] = len(shift1)
        ctx["shift_2_count"] = len(shift2)
        return (
            True,
            f"✅ Batch '{target_batch}' successfully partitioned into Shift 1 ({len(shift1)} students) and Shift 2 ({len(shift2)} students).",
            ctx,
        )

    return False, f"Unknown negotiation proposal ID: '{proposal_id}'", ctx


def simulate_what_if_scenario(
    students: List[StudentInfo],
    layouts: List[ClassroomLayout],
    student_multiplier: float = 1.0,
    disabled_room_ids: Optional[List[str]] = None,
    adjacency_mode: str = "horizontal_vertical",
) -> Dict[str, Any]:
    """
    Performs an instantaneous, non-destructive What-If stress test simulation.
    Tests hypothetical student volume surges, room closures, or constraint modifications.
    """
    disabled = set(disabled_room_ids or [])
    sim_layouts = [
        lay for lay in layouts
        if lay.is_available and lay.usable_seats > 0 and lay.room_id not in disabled
    ]

    sim_students_count = max(1, int(len(students) * student_multiplier))
    sim_seats_count = sum(lay.usable_seats for lay in sim_layouts)
    sim_rooms_count = len(sim_layouts)

    max_batch_cap = calculate_total_independent_capacity(sim_layouts, mode=adjacency_mode)

    batch_counts: Dict[str, int] = defaultdict(int)
    for s in students:
        batch_counts[s.batch] += 1
    scaled_batch_counts = {
        b: max(1, int(cnt * student_multiplier))
        for b, cnt in batch_counts.items()
    }

    bottlenecks = [
        {"batch": b, "count": cnt, "max_cap": max_batch_cap, "deficit": cnt - max_batch_cap}
        for b, cnt in scaled_batch_counts.items()
        if cnt > max_batch_cap
    ]

    seat_deficit = max(0, sim_students_count - sim_seats_count)
    is_feasible = (seat_deficit == 0) and (len(bottlenecks) == 0) and (sim_rooms_count > 0)

    return {
        "is_feasible": is_feasible,
        "sim_students_count": sim_students_count,
        "sim_seats_count": sim_seats_count,
        "sim_rooms_count": sim_rooms_count,
        "seat_deficit": seat_deficit,
        "seat_surplus": max(0, sim_seats_count - sim_students_count),
        "max_batch_capacity": max_batch_cap,
        "bottlenecks": bottlenecks,
        "adjacency_mode": adjacency_mode,
    }
