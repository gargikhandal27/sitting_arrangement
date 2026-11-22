"""
Unit tests for ExamFlow Copilot & Orchestration Agent.
"""
import pytest
from database.connection import get_db_session, init_db
from services.copilot_agent import handle_copilot_query, get_system_overview


@pytest.fixture(autouse=True)
def setup_database():
    init_db()


def test_copilot_empty_query():
    with get_db_session() as db:
        resp = handle_copilot_query("", db)
        assert resp.status == "info"
        assert "ExamFlow Copilot" in resp.message
        assert len(resp.suggested_prompts) > 0


def test_copilot_overview_query():
    with get_db_session() as db:
        resp = handle_copilot_query("Show system overview", db)
        assert resp.action_taken == "system_overview"
        assert "System Overview" in resp.message
        assert "Registered Students" in resp.message


def test_copilot_feasibility_query():
    with get_db_session() as db:
        resp = handle_copilot_query("Check seating feasibility", db)
        assert resp.action_taken == "feasibility_diagnosis"
        assert "Pre-Flight Feasibility" in resp.message


def test_copilot_batches_query():
    with get_db_session() as db:
        resp = handle_copilot_query("What batches are registered?", db)
        assert "Batches" in resp.message


def test_copilot_can_we_seat_query():
    with get_db_session() as db:
        resp = handle_copilot_query("can we seat all students", db)
        assert resp.action_taken == "feasibility_diagnosis"
        assert "Pre-Flight Feasibility" in resp.message


def test_copilot_auto_plan_query():
    with get_db_session() as db:
        from database.models import Classroom
        from sqlalchemy import update
        db.execute(update(Classroom).values(is_available=True))
        db.commit()

        resp = handle_copilot_query("Auto-plan exam with time limit 25 seconds", db)
        assert resp.status == "success"
        assert resp.action_taken == "execute_pipeline"
        assert "Successfully Generated" in resp.message

