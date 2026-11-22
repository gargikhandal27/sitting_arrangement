"""
Unit tests for Agent 2: Infeasibility Triage & Constraint Negotiation Agent.
Verifies negotiation proposal generation, confidence scoring, proposal execution,
What-If simulation, and checkerboard capacity analysis.
"""
import pytest
from database.connection import init_db, get_db_session
from database.models import Classroom, Student, Supervisor
from solvers.seating_solver import StudentInfo
from services.classroom_layout_service import ClassroomLayout, SeatInfo
from services.infeasibility_agent import (
    calculate_room_independent_capacity,
    calculate_total_independent_capacity,
    diagnose_seating_feasibility,
    apply_negotiation_proposal,
    simulate_what_if_scenario,
    get_classroom_checkerboard_analysis,
    RemediationOption,
    NegotiationProposal,
)


def _build_test_layout(room_id: str, rows: int, cols: int, is_available: bool = True) -> ClassroomLayout:
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


def test_negotiation_proposals_have_confidence_and_tradeoffs():
    # 12 students in CSE_A, but two 3x3 rooms can only take 10 students of CSE_A
    students = [
        StudentInfo(i, f"ST{i:03d}", f"Student_{i}", "CSE_A", str(100 + i))
        for i in range(1, 13)
    ]
    layouts = [_build_test_layout("R1", 3, 3), _build_test_layout("R2", 3, 3)]

    report = diagnose_seating_feasibility(students, layouts, adjacency_mode="horizontal_vertical")
    assert report.is_feasible is False
    assert len(report.remediations) > 0

    # Verify each negotiation proposal has confidence score and trade-off statement
    for p in report.proposals:
        assert isinstance(p, NegotiationProposal)
        assert 0.0 <= p.confidence_score <= 100.0
        assert len(p.trade_off) > 0
        assert len(p.impact) > 0

    # Ensure horizontal relaxation proposal is present with high confidence
    h_prop = next((p for p in report.proposals if p.id == "relax_to_horizontal"), None)
    assert h_prop is not None
    assert h_prop.confidence_score >= 80.0


def test_apply_relax_adjacency_proposal():
    config = {"adjacency_mode": "horizontal_vertical"}
    init_db()
    with get_db_session() as db:
        success, msg, updated = apply_negotiation_proposal("relax_to_horizontal", db, config)
        assert success is True
        assert updated["adjacency_mode"] == "horizontal"
        assert "relaxed" in msg.lower()


def test_apply_increase_time_limit_proposal():
    config = {"time_limit_seconds": 30}
    init_db()
    with get_db_session() as db:
        success, msg, updated = apply_negotiation_proposal("increase_time_limit", db, config)
        assert success is True
        assert updated["time_limit_seconds"] == 120


def test_apply_activate_rooms_proposal():
    init_db()
    with get_db_session() as db:
        # Create a temporary inactive room if needed
        room = db.query(Classroom).filter(Classroom.room_id == "TEST_NEGOTIATE_R99").first()
        if not room:
            room = Classroom(
                room_id="TEST_NEGOTIATE_R99",
                room_name="Test Inactive Negotiation Room",
                is_available=False,
            )
            db.add(room)
            db.commit()
        else:
            room.is_available = False
            db.commit()

        success, msg, updated = apply_negotiation_proposal("activate_inactive_rooms", db)
        assert success is True
        assert "activated" in msg.lower()

        # Verify room is now active in DB
        db.refresh(room)
        assert room.is_available is True

        # Clean up test room
        db.delete(room)
        db.commit()


def test_apply_split_batch_proposal():
    init_db()
    with get_db_session() as db:
        success, msg, updated = apply_negotiation_proposal("split_batch", db)
        if db.query(Student).filter(Student.is_active == True).count() > 0:
            assert success is True
            assert "split_batch" in updated
            assert updated["shift_1_count"] > 0
            assert updated["shift_2_count"] > 0


def test_simulate_what_if_scenario():
    students = [
        StudentInfo(i, f"ST{i:03d}", f"Student_{i}", "CSE_A", str(100 + i))
        for i in range(1, 21)  # 20 students
    ]
    layout1 = _build_test_layout("R1", 4, 4)  # 16 seats, max batch = 8
    layout2 = _build_test_layout("R2", 4, 4)  # 16 seats, max batch = 8
    # Total seats = 32, max batch = 16

    # Test baseline: 20 students vs max batch 16 -> Infeasible due to batch bottleneck
    baseline = simulate_what_if_scenario(students, [layout1, layout2], student_multiplier=1.0)
    assert baseline["is_feasible"] is False
    assert len(baseline["bottlenecks"]) > 0

    # Test relaxing to horizontal: max batch capacity per 4x4 room is 8, across 2 rooms = 16
    # Let's test with half students (multiplier=0.5 -> 10 students <= 16 max cap)
    scaled_down = simulate_what_if_scenario(students, [layout1, layout2], student_multiplier=0.5)
    assert scaled_down["is_feasible"] is True
    assert scaled_down["sim_students_count"] == 10

    # Test disabling room R2
    one_room = simulate_what_if_scenario(students, [layout1, layout2], disabled_room_ids=["R2"])
    assert one_room["sim_rooms_count"] == 1
    assert one_room["sim_seats_count"] == 16


def test_get_classroom_checkerboard_analysis():
    # 3x3 layout has 9 seats
    # (1,1)[0], (1,2)[1], (1,3)[0], (2,1)[1], (2,2)[0], (2,3)[1], (3,1)[0], (3,2)[1], (3,3)[0]
    # Color 0 = 5, Color 1 = 4.
    layout = _build_test_layout("R101", 3, 3)
    analysis = get_classroom_checkerboard_analysis([layout])

    assert len(analysis) == 1
    item = analysis[0]
    assert item["room_id"] == "R101"
    assert item["usable_seats"] == 9
    assert item["color_0"] == 5
    assert item["color_1"] == 4
    assert item["max_single_batch_hv"] == 5
    assert item["max_single_batch_h"] == 6
    assert item["bipartite_ratio_pct"] == round(5 / 9 * 100, 1)
