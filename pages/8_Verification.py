
"""
Independent Verification page (Phase 10)

Independently verifies seating and supervisor
assignments against hard constraints.
"""

import json
import importlib
import streamlit as st

import ui.theme
importlib.reload(ui.theme)
from ui.theme import apply_theme
from database.connection import init_db, get_db_session
from services.allocation_service import load_students_for_solver
from services.classroom_layout_service import get_all_layouts
from services.verification_service import verify_plan


# --------------------------------------------------
# PAGE SETUP
# --------------------------------------------------

apply_theme()
init_db()

st.title("✅ Independent Verification")

st.markdown(
    "Validate the generated seating arrangement and "
    "supervisor allocation against examination constraints. "
    "Verification is performed independently of the solver status."
)

st.divider()


# --------------------------------------------------
# LOAD SESSION DATA
# --------------------------------------------------

seating_result = st.session_state.get(
    "last_seating_result"
)

supervisor_result = st.session_state.get(
    "last_supervisor_result"
)

nl_config = st.session_state.get(
    "confirmed_nl_config",
    {}
)


# --------------------------------------------------
# CHECK SEATING PLAN
# --------------------------------------------------

if (
    seating_result is None
    or not getattr(seating_result, "assignments", None)
):

    st.warning(
        "No seating plan is available for verification."
    )

    st.info(
        "Generate a seating arrangement on Page 5 "
        "before running independent verification."
    )

else:

    # --------------------------------------------------
    # PLAN OVERVIEW
    # --------------------------------------------------

    st.header("Plan Overview")

    with st.container(border=True):

        st.markdown(
            "**Seating Plan:** Available"
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Students Assigned",
                seating_result.students_assigned,
            )

        with col2:
            st.metric(
                "Classrooms Used",
                seating_result.rooms_used,
            )

        with col3:
            st.metric(
                "Solver Status",
                seating_result.status,
            )

    # --------------------------------------------------
    # SUPERVISOR ALLOCATION STATUS
    # --------------------------------------------------

    st.subheader("Supervisor Allocation")

    if (
        supervisor_result is not None
        and getattr(supervisor_result, "assignments", None)
    ):

        st.success(
            "Supervisor allocation is available."
        )

        st.metric(
            "Supervisors Assigned",
            supervisor_result.total_assigned,
        )

    else:

        st.warning(
            "No supervisor allocation is available."
        )

        st.caption(
            "Seating verification can still run, "
            "but supervisor-related checks may be limited."
        )

    # --------------------------------------------------
    # VERIFICATION SETTINGS
    # --------------------------------------------------

    st.divider()
    st.header("Verification Settings")

    default_adjacency = nl_config.get(
        "adjacency_mode",
        "horizontal_vertical",
    )

    adjacency_options = [
        "horizontal_vertical",
        "horizontal",
    ]

    default_index = (
        adjacency_options.index(default_adjacency)
        if default_adjacency in adjacency_options
        else 0
    )

    default_ratio = (
        nl_config.get("students_per_supervisor", 30)
        or 30
    )

    default_ratio = max(
        1,
        min(100, int(default_ratio)),
    )

    with st.container(border=True):

        col1, col2 = st.columns(2)

        with col1:

            adjacency_mode = st.selectbox(
                "Adjacency Mode",
                options=adjacency_options,
                index=default_index,
                format_func=lambda value: {
                    "horizontal_vertical":
                        "Horizontal + Vertical",
                    "horizontal":
                        "Horizontal Only",
                }.get(value, value),
                help=(
                    "Select which neighboring seat positions "
                    "should be checked during verification."
                ),
            )

        with col2:

            students_per_supervisor = st.number_input(
                "Students per Supervisor",
                min_value=1,
                max_value=100,
                value=default_ratio,
                step=1,
                help=(
                    "Maximum number of students assigned "
                    "per required supervisor."
                ),
            )

        st.caption(
            "These settings determine which constraints "
            "the independent verification service evaluates."
        )

    # --------------------------------------------------
    # RUN VERIFICATION
    # --------------------------------------------------

    st.divider()
    st.header("Run Verification")

    st.markdown(
        "Check the latest seating arrangement and "
        "available supervisor assignments for constraint violations."
    )

    if st.button(
        "🔍 Run Independent Verification",
        type="primary",
        use_container_width=True,
    ):

        try:

            with st.spinner(
                "Running independent verification checks..."
            ):

                # Load current students and layouts.
                with get_db_session() as db:

                    students = load_students_for_solver(db)

                    expected_ids = {
                        student.external_id
                        for student in students
                    }

                    layouts = get_all_layouts(db)

                # Run existing verification service.
                report = verify_plan(
                    seating_assignments=(
                        seating_result.assignments
                    ),
                    supervisor_assignments=(
                        supervisor_result.assignments
                        if supervisor_result
                        else None
                    ),
                    layouts=layouts,
                    expected_student_ids=expected_ids,
                    adjacency_mode=adjacency_mode,
                    students_per_supervisor=int(
                        students_per_supervisor
                    ),
                )

            st.session_state[
                "last_verification_report"
            ] = report

        except Exception as error:

            st.error(
                f"Verification failed: {error}"
            )

    # --------------------------------------------------
    # VERIFICATION RESULTS
    # --------------------------------------------------

    report = st.session_state.get(
        "last_verification_report"
    )

    if report is not None:

        st.divider()
        st.header("Verification Results")

        # Overall status
        if report.overall_passed:

            st.success(
                "All verification checks passed."
            )

            st.markdown(
                report.summary
            )

        else:

            st.error(
                "Verification detected one or more issues."
            )

            st.markdown(
                report.summary
            )

        # --------------------------------------------------
        # SUMMARY METRICS
        # --------------------------------------------------

        checks = report.checks

        total_checks = len(checks)

        passed_checks = sum(
            1 for check in checks
            if check.passed
        )

        failed_checks = (
            total_checks - passed_checks
        )

        with st.container(border=True):

            st.subheader("Verification Summary")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Total Checks",
                    total_checks,
                )

            with col2:
                st.metric(
                    "Passed",
                    passed_checks,
                )

            with col3:
                st.metric(
                    "Failed",
                    failed_checks,
                )

        # --------------------------------------------------
        # INDIVIDUAL CHECKS
        # --------------------------------------------------

        st.divider()
        st.subheader("Individual Verification Checks")

        if not checks:

            st.info(
                "No individual verification checks "
                "were returned."
            )

        else:

            for check in checks:

                status_icon = (
                    "✅" if check.passed else "❌"
                )

                title = (
                    f"{status_icon} "
                    f"{check.name} — {check.message}"
                )

                with st.expander(
                    title,
                    expanded=not check.passed,
                ):

                    if check.passed:

                        st.success(
                            "This verification check passed."
                        )

                    else:

                        st.error(
                            "This verification check failed."
                        )

                    if check.violations:

                        st.markdown(
                            "**Detected Violations**"
                        )

                        for violation in check.violations:

                            st.write(
                                f"• {violation}"
                            )

                    else:

                        st.write(
                            "No violations reported."
                        )

        # --------------------------------------------------
        # DOWNLOAD VERIFICATION REPORT
        # --------------------------------------------------

        st.divider()
        st.subheader("Export Verification Report")

        report_dict = report.to_dict()

        json_data = json.dumps(
            report_dict,
            indent=2,
            ensure_ascii=False,
            default=str,
        )

        st.download_button(
            "⬇️ Download Verification Report (JSON)",
            data=json_data,
            file_name="verification_report.json",
            mime="application/json",
            use_container_width=True,
        )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "EXAMFLOW · Independent Verification"
)
