"""Unit tests for supervisor allocation."""
from solvers.supervisor_solver import (
    allocate_supervisors,
    calculate_required_supervisors,
    SupervisorInfo,
)


def test_required_calculation():
    assert calculate_required_supervisors(30, 30) == 1
    assert calculate_required_supervisors(31, 30) == 2
    assert calculate_required_supervisors(0, 30) == 0


def test_allocation_success():
    supervisors = [
        SupervisorInfo(1, "SUP1", "A", True),
        SupervisorInfo(2, "SUP2", "B", True),
        SupervisorInfo(3, "SUP3", "C", True),
    ]
    result = allocate_supervisors(
        room_student_counts={"R1": 40, "R2": 20},
        room_db_ids={"R1": 1, "R2": 2},
        supervisors=supervisors,
        students_per_supervisor=30,
    )
    assert result.success is True
    assert result.total_assigned >= 2


def test_allocation_shortage():
    supervisors = [
        SupervisorInfo(1, "SUP1", "A", True),
    ]
    result = allocate_supervisors(
        room_student_counts={"R1": 90},
        room_db_ids={"R1": 1},
        supervisors=supervisors,
        students_per_supervisor=30,
    )
    assert result.success is False
    assert len(result.shortages) > 0
