"""Unit tests for verification service."""
from services.verification_service import verify_plan
from services.classroom_layout_service import ClassroomLayout, SeatInfo


def _layout():
    seats = [
        SeatInfo(1, "R1C1", 1, "R1", 1, 1, True, True),
        SeatInfo(2, "R1C2", 1, "R1", 1, 2, True, True),
        SeatInfo(3, "R2C1", 1, "R1", 2, 1, True, True),
        SeatInfo(4, "R2C2", 1, "R1", 2, 2, True, True),
    ]
    return ClassroomLayout(1, "R1", "Room1", 2, 2, "test", True, seats)


def test_clean_plan_passes():
    """A clean seating plan with no supervisor data should still pass
    (supervisor check is skipped when no assignments are supplied)."""
    assignments = [
        {"student_id": "ST1", "batch": "A", "room_id": "R1", "seat_code": "R1C1", "row": 1, "column": 1},
        {"student_id": "ST2", "batch": "B", "room_id": "R1", "seat_code": "R1C2", "row": 1, "column": 2},
        {"student_id": "ST3", "batch": "A", "room_id": "R1", "seat_code": "R2C2", "row": 2, "column": 2},
    ]
    report = verify_plan(
        seating_assignments=assignments,
        supervisor_assignments=None,          # explicitly none → skip supervisor check
        layouts=[_layout()],
        expected_student_ids={"ST1", "ST2", "ST3"},
        adjacency_mode="horizontal_vertical",
    )
    assert report.overall_passed is True


def test_duplicate_student_fails():
    assignments = [
        {"student_id": "ST1", "batch": "A", "room_id": "R1", "seat_code": "R1C1", "row": 1, "column": 1},
        {"student_id": "ST1", "batch": "A", "room_id": "R1", "seat_code": "R1C2", "row": 1, "column": 2},
    ]
    report = verify_plan(
        seating_assignments=assignments,
        layouts=[_layout()],
        expected_student_ids={"ST1"},
    )
    assert report.overall_passed is False
