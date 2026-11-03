"""Unit tests for natural language interpreter."""
from services.natural_language_service import interpret_instruction


def test_full_instruction():
    text = (
        "Arrange seating for 400 students. "
        "Students from the same batch must not sit horizontally or vertically adjacent. "
        "Use as few classrooms as possible. "
        "One supervisor per 30 students."
    )
    result = interpret_instruction(text)
    assert result.success is True
    assert result.config.expected_students == 400
    assert result.config.adjacency_mode == "horizontal_vertical"
    assert result.config.minimize_classrooms is True
    assert result.config.students_per_supervisor == 30


def test_horizontal_only():
    text = "250 students. Same batch should not sit horizontally adjacent."
    result = interpret_instruction(text)
    assert result.config.expected_students == 250
    assert result.config.adjacency_mode == "horizontal"


def test_empty_instruction():
    result = interpret_instruction("")
    assert result.success is False


def test_unsupported_flagged():
    text = "Arrange 100 students with window seats for everyone."
    result = interpret_instruction(text)
    assert len(result.unsupported) > 0
