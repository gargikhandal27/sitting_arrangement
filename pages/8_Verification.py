"""
Independent Verification page (Phase 10)
"""
import streamlit as st
import pandas as pd

from database.connection import init_db, get_db_session
from services.allocation_service import load_students_for_solver
from services.classroom_layout_service import get_all_layouts
from services.verification_service import verify_plan

st.title("✅ Independent Verification")
st.markdown(
    "Re-checks the latest seating plan (and supervisor allocation) against all hard constraints. "
    "This module does **not** trust the solver status."
)

init_db()

seating_result = st.session_state.get("last_seating_result")
supervisor_result = st.session_state.get("last_supervisor_result")
nl_config = st.session_state.get("confirmed_nl_config", {})

if seating_result is None or not getattr(seating_result, "assignments", None):
    st.warning("No seating plan found in this session. Please run **Seating Generation** first.")
else:
    st.info(
        f"Seating plan loaded: {seating_result.students_assigned} students, "
        f"{seating_result.rooms_used} rooms, status = {seating_result.status}"
    )

    if supervisor_result and supervisor_result.assignments:
        st.info(f"Supervisor allocation loaded: {supervisor_result.total_assigned} supervisor(s) assigned.")
    else:
        st.caption("No supervisor allocation found – supervisor checks will be limited.")

    adjacency_mode = nl_config.get("adjacency_mode", "horizontal_vertical")
    students_per_supervisor = nl_config.get("students_per_supervisor", 30) or 30

    col1, col2 = st.columns(2)
    with col1:
        adjacency_mode = st.selectbox(
            "Adjacency mode to verify",
            options=["horizontal_vertical", "horizontal"],
            index=0 if adjacency_mode == "horizontal_vertical" else 1,
        )
    with col2:
        students_per_supervisor = st.number_input(
            "Students per supervisor (for verification)",
            min_value=1, max_value=100, value=int(students_per_supervisor),
        )

    if st.button("Run Independent Verification", type="primary"):
        with st.spinner("Running verification checks..."):
            with get_db_session() as db:
                students = load_students_for_solver(db)
                expected_ids = {s.external_id for s in students}
                layouts = get_all_layouts(db)

            report = verify_plan(
                seating_assignments=seating_result.assignments,
                supervisor_assignments=(
                    supervisor_result.assignments if supervisor_result else None
                ),
                layouts=layouts,
                expected_student_ids=expected_ids,
                adjacency_mode=adjacency_mode,
                students_per_supervisor=int(students_per_supervisor),
            )

        st.session_state["last_verification_report"] = report

        st.markdown("---")
        st.subheader("Verification Summary")

        if report.overall_passed:
            st.success(report.summary)
            st.balloons()
        else:
            st.error(report.summary)

        st.subheader("Individual Checks")
        for check in report.checks:
            icon = "✅" if check.passed else "❌"
            with st.expander(f"{icon} {check.name} — {check.message}", expanded=not check.passed):
                if check.violations:
                    for v in check.violations:
                        st.write(f"- {v}")
                else:
                    st.write("No violations.")

        # Downloadable report
        report_dict = report.to_dict()
        st.download_button(
            "Download verification report (JSON)",
            data=pd.Series(report_dict).to_json(indent=2),
            file_name="verification_report.json",
            mime="application/json",
        )
