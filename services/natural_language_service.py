"""
Natural Language Requirements Interpreter (Phase 7)

Controlled, rule-based parser – no external LLM required.
Extracts only supported examination constraints from English text
and returns a validated configuration object for administrator confirmation.
"""
from __future__ import annotations
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
import re


SUPPORTED_ADJACENCY_MODES = {
    "horizontal": "horizontal",
    "horizontal only": "horizontal",
    "horizontally": "horizontal",
    "horizontal and vertical": "horizontal_vertical",
    "horizontally and vertically": "horizontal_vertical",
    "horizontal_vertical": "horizontal_vertical",
    "both": "horizontal_vertical",
    "adjacent": "horizontal_vertical",  # default interpretation
}


@dataclass
class NLConfig:
    """Structured configuration extracted from natural language."""
    expected_students: Optional[int] = None
    adjacency_mode: Optional[str] = None          # "horizontal" | "horizontal_vertical"
    minimize_classrooms: Optional[bool] = None
    students_per_supervisor: Optional[int] = None
    solver_time_limit_seconds: Optional[int] = None
    exam_date: Optional[str] = None
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class InterpretationResult:
    success: bool
    config: NLConfig
    original_text: str
    extracted_items: List[str]          # human-readable list of what was understood
    warnings: List[str]
    unsupported: List[str]
    missing: List[str]
    requires_confirmation: bool = True


def _extract_number_near_keywords(text: str, keywords: List[str]) -> Optional[int]:
    """Find an integer near any of the given keywords."""
    text_lower = text.lower()
    for kw in keywords:
        # patterns like "400 students", "students: 400", "for 400 students"
        patterns = [
            rf"(\d+)\s*{kw}",
            rf"{kw}\s*[:=]?\s*(\d+)",
            rf"{kw}\s+(\d+)",
        ]
        for pat in patterns:
            m = re.search(pat, text_lower)
            if m:
                try:
                    return int(m.group(1))
                except ValueError:
                    continue
    return None


def interpret_instruction(text: str) -> InterpretationResult:
    """
    Main entry point.
    Parses supported English instructions into a structured NLConfig.
    """
    original = text.strip()
    if not original:
        return InterpretationResult(
            success=False,
            config=NLConfig(),
            original_text=original,
            extracted_items=[],
            warnings=["Empty instruction."],
            unsupported=[],
            missing=["All parameters"],
        )

    text_lower = original.lower()
    config = NLConfig()
    extracted: List[str] = []
    warnings: List[str] = []
    unsupported: List[str] = []
    missing: List[str] = []

    # 1. Expected number of students
    n_students = _extract_number_near_keywords(
        text_lower,
        ["students", "student", "candidates", "examinees"]
    )
    if n_students is not None:
        if n_students <= 0:
            warnings.append(f"Student count {n_students} is not positive.")
        else:
            config.expected_students = n_students
            extracted.append(f"Expected students: {n_students}")

    # 2. Adjacency / batch separation mode
    if any(p in text_lower for p in [
        "same batch", "same-batch", "batch separation", "not sit next",
        "not sit adjacent", "must not sit", "should not sit",
        "separate students from the same batch", "no two students from same batch"
    ]):
        if any(p in text_lower for p in [
            "horizontally and vertically", "horizontal and vertical",
            "horizontal or vertical", "both directions", "adjacent in any direction"
        ]):
            config.adjacency_mode = "horizontal_vertical"
            extracted.append("Adjacency mode: horizontal + vertical (same batch cannot sit next to each other in row or column)")
        elif "horizontal" in text_lower and "vertical" not in text_lower:
            config.adjacency_mode = "horizontal"
            extracted.append("Adjacency mode: horizontal only")
        else:
            # default to strongest common requirement
            config.adjacency_mode = "horizontal_vertical"
            extracted.append("Adjacency mode: horizontal + vertical (default interpretation)")
            warnings.append("Adjacency direction was not fully explicit – assumed horizontal + vertical.")

    # 3. Minimize number of classrooms
    if any(p in text_lower for p in [
        "minimize classroom", "minimise classroom", "as few classroom",
        "fewest classroom", "use as few", "minimum rooms", "minimize rooms",
        "least number of classroom", "least classrooms"
    ]):
        config.minimize_classrooms = True
        extracted.append("Minimize number of classrooms: Yes")

    # 4. Supervisors policy
    # patterns: "one supervisor per 30 students", "1 supervisor for every 30", "supervisor per 30"
    sup_match = re.search(
        r"(?:one|1)\s*supervisor\s*(?:per|for every|for each|per every)?\s*(\d+)\s*students?",
        text_lower
    )
    if not sup_match:
        sup_match = re.search(
            r"supervisor\s*(?:per|for every|for each)\s*(\d+)\s*students?",
            text_lower
        )
    if not sup_match:
        # "30 students per supervisor"
        sup_match = re.search(
            r"(\d+)\s*students?\s*per\s*supervisor",
            text_lower
        )

    if sup_match:
        try:
            val = int(sup_match.group(1))
            if val > 0:
                config.students_per_supervisor = val
                extracted.append(f"Students per supervisor: {val}")
            else:
                warnings.append("Students-per-supervisor value must be positive.")
        except ValueError:
            pass

    # 5. Solver time limit (optional)
    time_match = re.search(
        r"(?:time\s*limit|solver\s*time|maximum\s*time|timeout)\s*(?:of\s*)?(\d+)\s*(?:seconds?|secs?|s)?",
        text_lower
    )
    if time_match:
        try:
            t = int(time_match.group(1))
            if 5 <= t <= 600:
                config.solver_time_limit_seconds = t
                extracted.append(f"Solver time limit: {t} seconds")
            else:
                warnings.append("Solver time limit should be between 5 and 600 seconds.")
        except ValueError:
            pass

    # Detect clearly unsupported requests (examples)
    unsupported_patterns = [
        (r"window\s*seat", "Window-seat preference is not supported."),
        (r"front\s*row", "Front-row preference is not supported."),
        (r"left[- ]handed", "Left-handed seating is not supported."),
        (r"disability|special\s*need", "Special-needs seating must be handled by marking seats unavailable manually."),
        (r"random(ly)?\s*seat", "Fully random seating without constraints is not a supported mode."),
    ]
    for pat, msg in unsupported_patterns:
        if re.search(pat, text_lower):
            unsupported.append(msg)

    # Determine missing important fields
    if config.expected_students is None:
        missing.append("Number of students")
    if config.adjacency_mode is None:
        missing.append("Batch separation / adjacency rule")
    if config.students_per_supervisor is None:
        missing.append("Supervisor policy (students per supervisor)")

    success = len(extracted) > 0

    return InterpretationResult(
        success=success,
        config=config,
        original_text=original,
        extracted_items=extracted,
        warnings=warnings,
        unsupported=unsupported,
        missing=missing,
        requires_confirmation=True,
    )


def config_to_human_summary(config: NLConfig) -> str:
    """Produce a short human-readable summary of the configuration."""
    lines = []
    if config.expected_students is not None:
        lines.append(f"• Expected students: {config.expected_students}")
    if config.adjacency_mode:
        mode_txt = "Horizontal only" if config.adjacency_mode == "horizontal" else "Horizontal + Vertical"
        lines.append(f"• Batch separation: {mode_txt}")
    if config.minimize_classrooms:
        lines.append("• Minimize number of classrooms: Yes")
    if config.students_per_supervisor:
        lines.append(f"• Supervisor policy: 1 supervisor per {config.students_per_supervisor} students")
    if config.solver_time_limit_seconds:
        lines.append(f"• Solver time limit: {config.solver_time_limit_seconds} seconds")
    if not lines:
        return "No supported settings could be extracted."
    return "\n".join(lines)
