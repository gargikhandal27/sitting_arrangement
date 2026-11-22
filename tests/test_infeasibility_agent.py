"""
Unit tests for AI Infeasibility Diagnostic & Negotiation Agent.
"""
import pytest
from solvers.seating_solver import StudentInfo, SolverResult
from services.classroom_layout_service import ClassroomLayout, SeatInfo
from services.infeasibility_agent import (
    calculate_room_independent_capacity,
    calculate_total_independent_capacity,
    diagnose_seating_feasibility,
)


def _make_layout(room_id: str, rows: int, cols: int, is_available: bool = True) -> ClassroomLayout:
    seats = []
    sid = 1
    for r in range(1, rows + 1):
        for c in range(1, cols + 1):
            seats.append(SeatInfo(
                seat_id=sid,
                seat_code=f"R{r}C{c}",
                classroom_id=1,
                room_id=room_id,
                row=r,
                col=c,
                is_available=True,
                is_confirmed=True,
            ))
            sid += 1
    return ClassroomLayout(
        classroom_id=1,
        room_id=room_id,
        room_name=room_id,
        rows=rows,
        columns=cols,
        layout_source="test",
        is_available=is_available,
        seats=seats,
    )


def test_independent_capacity_calculation():
    # 4x4 grid = 16 seats
    layout = _make_layout("R1", 4, 4)
    # Checkerboard independent set of 4x4 is 8
    cap_hv = calculate_room_independent_capacity(layout, mode="horizontal_vertical")
    assert cap_hv == 8

    # Horizontal only: each row of 4 seats can take ceil(4/2) = 2 seats. 4 rows * 2 = 8.
    cap_h = calculate_room_independent_capacity(layout, mode="horizontal")
    assert cap_h == 8

    # 3x3 grid = 9 seats
    # Color 0 (even r+c): (1,1), (1,3), (2,2), (3,1), (3,3) = 5 seats
    # Color 1 (odd r+c): (1,2), (2,1), (2,3), (3,2) = 4 seats
    layout_3x3 = _make_layout("R2", 3, 3)
    cap_3x3_hv = calculate_room_independent_capacity(layout_3x3, mode="horizontal_vertical")
    assert cap_3x3_hv == 5

    # Horizontal only for 3x3: ceil(3/2)*3 = 2*3 = 6 seats
    cap_3x3_h = calculate_room_independent_capacity(layout_3x3, mode="horizontal")
    assert cap_3x3_h == 6


def test_diagnose_feasible_instance():
    students = [
        StudentInfo(1, "ST001", "Alice", "CSE_A", "101"),
        StudentInfo(2, "ST002", "Bob", "CSE_B", "102"),
        StudentInfo(3, "ST003", "Charlie", "CSE_A", "103"),
        StudentInfo(4, "ST004", "David", "CSE_B", "104"),
    ]
    layout = _make_layout("R1", 3, 3)  # 9 seats, max single-batch cap = 5
    report = diagnose_seating_feasibility(students, [layout], adjacency_mode="horizontal_vertical")

    assert report.is_feasible is True
    assert report.total_students == 4
    assert report.total_usable_seats == 9
    assert len(report.issues) == 0


def test_diagnose_global_capacity_deficit():
    students = [
        StudentInfo(i, f"ST{i:03d}", f"Student_{i}", "CSE_A", str(100 + i))
        for i in range(1, 15)  # 14 students
    ]
    layout = _make_layout("R1", 2, 3)  # only 6 seats
    report = diagnose_seating_feasibility(students, [layout], adjacency_mode="horizontal_vertical")

    assert report.is_feasible is False
    assert any(i.category == "GLOBAL_CAPACITY" for i in report.issues)
    assert report.issues[0].details["deficit"] == 8


def test_diagnose_batch_bottleneck_and_remediation():
    # 10 students from CSE_A, but a 3x3 room can only seat 5 students from CSE_A under horizontal_vertical
    # Total room seats = 9 (or let's provide two 3x3 rooms = 18 seats, but CSE_A has 12 students.
    # Total capacity = 18 >= 12, so global capacity is sufficient.
    # BUT max independent set across two 3x3 rooms is 5 + 5 = 10 < 12!
    students = [
        StudentInfo(i, f"ST{i:03d}", f"Student_{i}", "CSE_A", str(100 + i))
        for i in range(1, 13)  # 12 students of same batch
    ]
    layout1 = _make_layout("R1", 3, 3)
    layout2 = _make_layout("R2", 3, 3)

    report = diagnose_seating_feasibility(students, [layout1, layout2], adjacency_mode="horizontal_vertical")

    assert report.is_feasible is False
    assert any(i.category == "BATCH_BOTTLENECK" for i in report.issues)
    # Check that remediation proposing horizontal only was generated
    assert any(r.action_type == "relax_adjacency" for r in report.remediations)
