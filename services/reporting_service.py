"""
Reporting Service (Phase 12)
Generates downloadable CSV / Excel reports for seating plans.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import pandas as pd

from config import REPORTS_DIR


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def generate_student_seating_report(
    assignments: List[Dict[str, Any]],
    session_name: str = "exam",
) -> Path:
    """Student seating report → CSV + Excel."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(assignments)

    # Preferred column order
    cols = [
        "student_id", "roll_number", "student_name", "batch",
        "room_id", "seat_code", "row", "column"
    ]
    existing = [c for c in cols if c in df.columns]
    extra = [c for c in df.columns if c not in existing]
    df = df[existing + extra]

    stem = f"student_seating_{session_name}_{_timestamp()}"
    csv_path = REPORTS_DIR / f"{stem}.csv"
    xlsx_path = REPORTS_DIR / f"{stem}.xlsx"

    df.to_csv(csv_path, index=False)
    df.to_excel(xlsx_path, index=False)
    return xlsx_path


def generate_supervisor_report(
    assignments: List[Dict[str, Any]],
    session_name: str = "exam",
) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(assignments)
    stem = f"supervisor_allocation_{session_name}_{_timestamp()}"
    xlsx_path = REPORTS_DIR / f"{stem}.xlsx"
    df.to_excel(xlsx_path, index=False)
    df.to_csv(REPORTS_DIR / f"{stem}.csv", index=False)
    return xlsx_path


def generate_classroom_report(
    layouts_summary: List[Dict[str, Any]],
    assignments: List[Dict[str, Any]],
    session_name: str = "exam",
) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Count assigned students per room
    from collections import Counter
    room_counts = Counter(a["room_id"] for a in assignments)

    rows = []
    for lay in layouts_summary:
        rows.append({
            "room_id": lay.get("room_id"),
            "room_name": lay.get("room_name"),
            "layout_source": lay.get("layout_source"),
            "total_seats": lay.get("total_seats"),
            "usable_seats": lay.get("usable_seats"),
            "assigned_students": room_counts.get(lay.get("room_id"), 0),
            "confirmed": lay.get("confirmed"),
            "is_available": lay.get("is_available"),
        })

    df = pd.DataFrame(rows)
    stem = f"classroom_report_{session_name}_{_timestamp()}"
    xlsx_path = REPORTS_DIR / f"{stem}.xlsx"
    df.to_excel(xlsx_path, index=False)
    df.to_csv(REPORTS_DIR / f"{stem}.csv", index=False)
    return xlsx_path


def generate_ai_processing_report(
    nl_config: Optional[Dict[str, Any]],
    seating_status: str,
    seating_runtime: float,
    rooms_used: int,
    students_assigned: int,
    verification_passed: Optional[bool],
    image_method: str = "opencv_contours / manual",
    session_name: str = "exam",
) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    data = {
        "timestamp": datetime.now().isoformat(),
        "session_name": session_name,
        "nl_config": nl_config or {},
        "image_processing_method": image_method,
        "solver_status": seating_status,
        "solver_runtime_seconds": seating_runtime,
        "rooms_used": rooms_used,
        "students_assigned": students_assigned,
        "verification_passed": verification_passed,
    }

    # Flatten for a simple one-row Excel
    flat = {
        "timestamp": data["timestamp"],
        "session_name": session_name,
        "expected_students": (nl_config or {}).get("expected_students"),
        "adjacency_mode": (nl_config or {}).get("adjacency_mode"),
        "minimize_classrooms": (nl_config or {}).get("minimize_classrooms"),
        "students_per_supervisor": (nl_config or {}).get("students_per_supervisor"),
        "solver_status": seating_status,
        "solver_runtime_seconds": seating_runtime,
        "rooms_used": rooms_used,
        "students_assigned": students_assigned,
        "verification_passed": verification_passed,
        "image_processing_method": image_method,
    }
    df = pd.DataFrame([flat])
    stem = f"ai_processing_report_{session_name}_{_timestamp()}"
    xlsx_path = REPORTS_DIR / f"{stem}.xlsx"
    df.to_excel(xlsx_path, index=False)
    return xlsx_path
