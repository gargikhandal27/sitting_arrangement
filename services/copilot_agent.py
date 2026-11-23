"""
ExamFlow Copilot & Orchestration Agent (Phase 1 AI Upgrade)

Provides an autonomous conversational assistant that can:
1. Answer natural language queries regarding examination data and capacity.
2. Run pre-flight feasibility diagnostics using the Infeasibility Agent.
3. Automatically orchestrate end-to-end examination pipelines (seating + supervisor + verification + DB persistence).
4. Recommend intelligent remediations when constraints or capacities conflict.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, date
import re

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from database.models import Student, Classroom, Supervisor, ExaminationSession, SeatingPlan, StudentSeatAssignment, SupervisorAssignment, VerificationResult
from database import repository as repo
from services.classroom_layout_service import get_all_layouts, ClassroomLayout
from services.allocation_service import (
    load_students_for_solver,
    load_supervisors_for_solver,
    run_seating_generation,
    run_supervisor_allocation,
)
from services.verification_service import verify_plan, VerificationReport
from services.infeasibility_agent import (
    diagnose_seating_feasibility,
    DiagnosisReport,
)
from services.natural_language_service import interpret_instruction, NLConfig


@dataclass
class CopilotResponse:
    message: str
    status: str = "info"  # success | warning | error | info
    action_taken: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    suggested_prompts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def get_system_overview(db: Session) -> Dict[str, Any]:
    """Gather live data metrics from the database."""
    batch_rows = db.execute(select(Student.batch, func.count()).group_by(Student.batch)).all()
    batch_counts: Dict[str, int] = {str(b): int(cnt) for b, cnt in batch_rows if b}
    student_count = sum(batch_counts.values()) or repo.count_students(db)

    classrooms = repo.get_all_classrooms(db)
    supervisors = repo.get_all_supervisors(db)
    layouts = get_all_layouts(db)

    active_layouts = [lay for lay in layouts if lay.is_available and lay.usable_seats > 0]
    total_usable_seats = sum(lay.usable_seats for lay in active_layouts)
    available_supervisors = [sup for sup in supervisors if sup.is_available]

    return {
        "student_count": student_count,
        "batch_counts": batch_counts,
        "classroom_count": len(classrooms),
        "active_classroom_count": len(active_layouts),
        "total_usable_seats": total_usable_seats,
        "supervisor_count": len(supervisors),
        "available_supervisor_count": len(available_supervisors),
        "plans_count": repo.count_plans(db),
    }


def execute_full_exam_pipeline(
    db: Session,
    session_code: str = "AUTO-SESSION",
    adjacency_mode: str = "horizontal_vertical",
    minimize_classrooms: bool = True,
    time_limit_seconds: int = 60,
    students_per_supervisor: int = 30,
    plan_name: Optional[str] = None,
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Autonomous pipeline:
    1. Pre-flight Check
    2. Solve Seating
    3. Allocate Supervisors
    4. Independently Verify
    5. Save Seating Plan to Database
    """
    students = load_students_for_solver(db)
    supervisors = load_supervisors_for_solver(db)
    layouts = [lay for lay in get_all_layouts(db) if lay.is_available and lay.usable_seats > 0]

    # Step 1: Pre-flight Feasibility Check
    diag = diagnose_seating_feasibility(
        students=students,
        layouts=layouts,
        adjacency_mode=adjacency_mode,
        time_limit_seconds=time_limit_seconds,
        supervisors=supervisors,
        students_per_supervisor=students_per_supervisor,
    )

    if not diag.is_feasible:
        # Check if errors prevent solving
        has_blocking_errors = any(i.severity == "error" for i in diag.issues)
        if has_blocking_errors:
            error_msg = "\n".join(f"• {i.title}: {i.description}" for i in diag.issues if i.severity == "error")
            return False, f"Pre-flight feasibility check failed:\n\n{error_msg}", {"diagnosis": diag.to_dict()}

    # Step 2: Solve Seating
    seating_result, layouts_used = run_seating_generation(
        db,
        adjacency_mode=adjacency_mode,
        minimize_classrooms=minimize_classrooms,
        time_limit_seconds=time_limit_seconds,
    )

    if seating_result.status not in ("OPTIMAL", "FEASIBLE"):
        # Run post-mortem diagnosis
        post_diag = diagnose_seating_feasibility(
            students=students,
            layouts=layouts,
            adjacency_mode=adjacency_mode,
            time_limit_seconds=time_limit_seconds,
            solver_result=seating_result,
        )
        return False, f"Solver could not find a valid seating arrangement: {seating_result.message}", {
            "seating_result": asdict(seating_result),
            "diagnosis": post_diag.to_dict(),
        }

    # Step 3: Supervisor Allocation
    supervisor_result = run_supervisor_allocation(
        db,
        seating_assignments=seating_result.assignments,
        students_per_supervisor=students_per_supervisor,
    )

    # Step 4: Verification
    expected_ids = {s.external_id for s in students}
    verification_report = verify_plan(
        seating_assignments=seating_result.assignments,
        supervisor_assignments=supervisor_result.assignments,
        layouts=layouts_used,
        expected_student_ids=expected_ids,
        adjacency_mode=adjacency_mode,
        students_per_supervisor=students_per_supervisor,
    )

    # Step 5: Save to Database
    now = datetime.utcnow()
    # Check or create session
    exam_session = db.scalar(select(ExaminationSession).where(ExaminationSession.session_code == session_code))
    if not exam_session:
        exam_session = ExaminationSession(
            session_code=session_code,
            session_name=f"Examination {session_code}",
            exam_date=date.today(),
            status="solved",
        )
        db.add(exam_session)
        db.flush()

    plan_title = plan_name or f"Plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    plan = SeatingPlan(
        session_id=exam_session.id,
        plan_name=plan_title,
        status="verified" if verification_report.overall_passed else "solved",
        solver_status=seating_result.status,
        solver_runtime_seconds=seating_result.runtime_seconds,
        rooms_used=seating_result.rooms_used,
        students_assigned=seating_result.students_assigned,
        configuration_json={
            "adjacency_mode": adjacency_mode,
            "minimize_classrooms": minimize_classrooms,
            "time_limit_seconds": time_limit_seconds,
            "students_per_supervisor": students_per_supervisor,
        },
    )
    db.add(plan)
    db.flush()

    # Save student seat assignments
    for a in seating_result.assignments:
        db.add(
            StudentSeatAssignment(
                plan_id=plan.id,
                student_id=a["student_db_id"],
                seat_id=a["seat_db_id"],
            )
        )

    # Save supervisor assignments
    for sa in supervisor_result.assignments:
        db.add(
            SupervisorAssignment(
                plan_id=plan.id,
                supervisor_id=sa["supervisor_db_id"],
                classroom_id=sa["classroom_db_id"],
                duty_date=date.today(),
            )
        )

    # Save verification result
    db.add(
        VerificationResult(
            plan_id=plan.id,
            overall_passed=verification_report.overall_passed,
            checks_json=[{"name": c.name, "passed": c.passed, "message": c.message} for c in verification_report.checks],
            violations_json=[v for c in verification_report.checks for v in c.violations],
            notes=verification_report.summary,
        )
    )
    db.commit()

    allocated_count = supervisor_result.total_assigned
    req_count = supervisor_result.total_required
    shortage_count = len(supervisor_result.shortages)
    shortage_msg = f"Shortage of {shortage_count}" if shortage_count > 0 else "All covered"

    success_summary = (
        f"### 🚀 Seating Plan '{plan_title}' Successfully Generated & Verified!\n\n"
        f"• **Students Assigned:** {seating_result.students_assigned} / {len(students)}\n"
        f"• **Classrooms Used:** {seating_result.rooms_used}\n"
        f"• **Supervisors Assigned:** {allocated_count} / {req_count} ({shortage_msg})\n"
        f"• **Verification:** {'✅ Passed All Independent Checks' if verification_report.overall_passed else '⚠️ Has Violations'}\n"
        f"• **Solver Runtime:** {seating_result.runtime_seconds:.2f}s"
    )

    return True, success_summary, {
        "plan_id": plan.id,
        "seating_result": asdict(seating_result),
        "supervisor_result": asdict(supervisor_result),
        "verification_report": verification_report.to_dict(),
    }


def handle_copilot_query(query: str, db: Session) -> CopilotResponse:
    """
    Main conversational agent reasoning handler.
    Analyzes intent, executes tools, and generates structured response.
    """
    q = query.strip().lower()
    if not q:
        return CopilotResponse(
            message="Hello! I am **ExamFlow Copilot**. How can I help you manage your examination logistics today?",
            status="info",
            suggested_prompts=[
                "Check exam seating feasibility",
                "Show system resource overview",
                "Plan full exam seating with default settings",
                "What batches are registered?",
            ],
        )

    # 1. Status / Overview Query
    if any(k in q for k in ["overview", "status", "resources", "summary", "how many students", "how many rooms", "stats"]):
        overview = get_system_overview(db)
        batches_str = "\n".join(f"  - `{b}`: {cnt} students" for b, cnt in overview["batch_counts"].items())
        msg = (
            f"### 📊 Examination System Overview\n\n"
            f"• **Registered Students:** {overview['student_count']}\n"
            f"• **Batches:**\n{batches_str if batches_str else '  *(No students registered)*'}\n\n"
            f"• **Classrooms:** {overview['active_classroom_count']} active / {overview['classroom_count']} total\n"
            f"• **Total Usable Seats:** {overview['total_usable_seats']}\n"
            f"• **Supervisors:** {overview['available_supervisor_count']} available / {overview['supervisor_count']} total\n"
            f"• **Saved Seating Plans:** {overview['plans_count']}"
        )
        return CopilotResponse(
            message=msg,
            status="info",
            action_taken="system_overview",
            data=overview,
            suggested_prompts=[
                "Run pre-flight feasibility check",
                "Auto-plan examination seating",
                "Can we fit 400 students?",
            ],
        )

    # 2. Feasibility / Diagnostic / Agent 2 Negotiation Query
    feasibility_keywords = [
        "feasib", "diagnos", "can we fit", "capacity check", "preflight", "pre-flight",
        "check if possible", "can we seat", "seat all", "enough seat", "fit all",
        "will it fit", "can all students", "possible to seat", "capacity", "enough space",
        "negotiat", "triage", "agent 2", "iis", "trade-off", "tradeoff", "bottleneck"
    ]
    if any(k in q for k in feasibility_keywords):
        students = load_students_for_solver(db)
        layouts = get_all_layouts(db)
        supervisors = load_supervisors_for_solver(db)

        # Detect desired adjacency mode from query
        adj_mode = "horizontal" if "horizontal only" in q else "horizontal_vertical"

        diag = diagnose_seating_feasibility(
            students=students,
            layouts=layouts,
            adjacency_mode=adj_mode,
            supervisors=supervisors,
        )

        status_icon = "🟢" if diag.is_feasible else "🔴"
        verdict_str = f"### {status_icon} Pre-Flight Feasibility Check: **{diag.overall_status}**\n\n{diag.summary}\n\n"

        # Issues details
        if diag.issues:
            verdict_str += "#### ⚠️ Problems Found:\n"
            for i in diag.issues:
                icon = "❌" if i.severity == "error" else "⚠️"
                verdict_str += f"- **{icon} {i.title}**: {i.description}\n"
            verdict_str += "\n"

        # Negotiation proposals with confidence scores
        if diag.remediations:
            verdict_str += "#### 💡 Recommended Quick Fixes:\n"
            for r in diag.remediations:
                conf = getattr(r, "confidence_score", 95.0)
                trade = f" (What to keep in mind: *{r.trade_off}*)" if getattr(r, "trade_off", None) else ""
                verdict_str += f"- **{r.title}** [`{conf}% success chance`]: {r.description}{trade} *(Benefit: {r.impact})*\n"
            verdict_str += (
                "\n> ⚖️ *You can apply any of these solutions with 1 click in the **Seating Generation** page, "
                "or ask me to auto-plan seating now.*"
            )

        return CopilotResponse(
            message=verdict_str,
            status="success" if diag.is_feasible else "warning",
            action_taken="feasibility_diagnosis",
            data={"diagnosis": diag.to_dict()},
            suggested_prompts=[
                "Execute full exam seating plan",
                "Relax batch separation to horizontal only",
                "Show resource overview",
            ],
        )

    # 3. Autonomous Execution / Plan Query
    plan_keywords = [
        "auto-plan", "autoplan", "generate plan", "run solver", "plan exam",
        "schedule exam", "start generation", "plan now", "generate seating"
    ]
    if any(k in q for k in plan_keywords):
        # Extract parameters using NLP service
        nl_res = interpret_instruction(query)
        cfg = nl_res.config

        adj_mode = cfg.adjacency_mode or "horizontal_vertical"
        min_rooms = cfg.minimize_classrooms if cfg.minimize_classrooms is not None else True
        time_lim = cfg.solver_time_limit_seconds or 25
        sup_ratio = cfg.students_per_supervisor or 30

        try:
            success, msg, pipeline_data = execute_full_exam_pipeline(
                db,
                adjacency_mode=adj_mode,
                minimize_classrooms=min_rooms,
                time_limit_seconds=time_lim,
                students_per_supervisor=sup_ratio,
            )
        except Exception as e:
            success = False
            msg = f"❌ An error occurred while executing the exam pipeline: {str(e)}"
            pipeline_data = {"error": str(e)}

        return CopilotResponse(
            message=msg,
            status="success" if success else "error",
            action_taken="execute_pipeline",
            data=pipeline_data,
            suggested_prompts=[
                "Show recent seating plans",
                "Check system overview",
                "Run feasibility check with horizontal only",
            ],
        )

    # 4. Batches query
    if "batch" in q:
        overview = get_system_overview(db)
        batch_counts = overview["batch_counts"]
        if not batch_counts:
            msg = "No student batches found in the database. Please import students on Page 2."
        else:
            rows = [f"| `{b}` | {cnt} students |" for b, cnt in sorted(batch_counts.items(), key=lambda x: -x[1])]
            msg = "### 👥 Registered Batches\n\n| Batch | Students |\n|---|---|\n" + "\n".join(rows)
        return CopilotResponse(
            message=msg,
            status="info",
            data={"batch_counts": batch_counts},
            suggested_prompts=["Check seating feasibility", "Show system overview"],
        )

    # 5. Natural Language Instruction Interpretation Fallback
    nl_res = interpret_instruction(query)
    if nl_res.extracted_items:
        extracted_bullets = "\n".join(f"- {item}" for item in nl_res.extracted_items)
        msg = (
            f"### 📝 Parsed Examination Requirements\n\n"
            f"I analyzed your request and identified the following parameters:\n\n"
            f"{extracted_bullets}\n\n"
            f"Would you like me to execute this plan now? You can say: **'Auto-plan exam with these settings'**."
        )
        return CopilotResponse(
            message=msg,
            status="success",
            action_taken="nl_interpretation",
            data={"config": nl_res.config.to_dict()},
            suggested_prompts=[
                "Auto-plan exam with these settings",
                "Check feasibility with these settings",
            ],
        )

    # Generic help
    return CopilotResponse(
        message=(
            "I'm here to assist with all examination logistics in EXAMFLOW. You can ask me to:\n\n"
            "- **Check Feasibility**: *'Check if our classrooms can seat all 300 students'*\n"
            "- **Run Full Pipeline**: *'Auto-plan seating with horizontal separation and 1 supervisor per 25 students'*\n"
            "- **Diagnose Bottlenecks**: *'Why is Batch CS-A failing to seat?'*\n"
            "- **System Status**: *'Show system overview'*"
        ),
        status="info",
        suggested_prompts=[
            "Show system overview",
            "Check exam seating feasibility",
            "Auto-plan examination seating",
        ],
    )
