"""Unit tests for seating solver (small instances)."""
from solvers.seating_solver import solve_seating, StudentInfo
from services.classroom_layout_service import ClassroomLayout, SeatInfo


def _make_layout(room_id: str, rows: int, cols: int) -> ClassroomLayout:
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
        is_available=True,
        seats=seats,
    )


def test_basic_feasible():
    students = [
        StudentInfo(1, "ST001", "A", "CSE_A", "101"),
        StudentInfo(2, "ST002", "B", "CSE_B", "102"),
        StudentInfo(3, "ST003", "C", "CSE_A", "103"),
        StudentInfo(4, "ST004", "D", "CSE_B", "104"),
    ]
    layout = _make_layout("R1", 2, 3)  # 6 seats
    result = solve_seating(
        students=students,
        layouts=[layout],
        adjacency_mode="horizontal_vertical",
        minimize_classrooms=False,
        time_limit_seconds=10,
    )
    assert result.status in ("OPTIMAL", "FEASIBLE")
    assert result.students_assigned == 4


def test_insufficient_capacity():
    students = [
        StudentInfo(i, f"ST{i:03d}", f"S{i}", "CSE_A", str(100+i))
        for i in range(1, 10)
    ]
    layout = _make_layout("R1", 2, 2)  # only 4 seats
    result = solve_seating(
        students=students,
        layouts=[layout],
        time_limit_seconds=5,
    )
    assert result.status == "INFEASIBLE"
