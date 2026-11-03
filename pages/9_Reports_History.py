"""
Reports & History page (Phase 12)
"""
import streamlit as st
import pandas as pd
from pathlib import Path

from database.connection import init_db, get_db_session
from services.classroom_layout_service import get_layout_summary
from services.reporting_service import (
    generate_student_seating_report,
    generate_supervisor_report,
    generate_classroom_report,
    generate_ai_processing_report,
)
from config import REPORTS_DIR

st.title("📄 Reports & History")
st.markdown("Generate and download reports for the latest plan.")

init_db()

seating_result = st.session_state.get("last_seating_result")
supervisor_result = st.session_state.get("last_supervisor_result")
verification_report = st.session_state.get("last_verification_report")
nl_config = st.session_state.get("confirmed_nl_config", {})

tab_export, tab_history = st.tabs(["Export Reports", "Generated Files"])

with tab_export:
    if seating_result is None or not getattr(seating_result, "assignments", None):
        st.warning("No seating plan available. Run Seating Generation first.")
    else:
        st.success(
            f"Plan ready: {seating_result.students_assigned} students, "
            f"{seating_result.rooms_used} rooms, status = {seating_result.status}"
        )

        session_name = st.text_input("Session / Exam name (for filenames)", value="exam_session")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Generate Student Seating Report", type="primary"):
                path = generate_student_seating_report(
                    seating_result.assignments, session_name=session_name
                )
                st.success(f"Created: {path.name}")
                with open(path, "rb") as f:
                    st.download_button(
                        "Download Student Seating (Excel)",
                        f,
                        file_name=path.name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )

            if st.button("Generate Classroom Report"):
                with get_db_session() as db:
                    summaries = get_layout_summary(db)
                path = generate_classroom_report(
                    summaries, seating_result.assignments, session_name=session_name
                )
                st.success(f"Created: {path.name}")
                with open(path, "rb") as f:
                    st.download_button(
                        "Download Classroom Report (Excel)",
                        f,
                        file_name=path.name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )

        with col2:
            if st.button("Generate Supervisor Report"):
                if supervisor_result and supervisor_result.assignments:
                    path = generate_supervisor_report(
                        supervisor_result.assignments, session_name=session_name
                    )
                    st.success(f"Created: {path.name}")
                    with open(path, "rb") as f:
                        st.download_button(
                            "Download Supervisor Report (Excel)",
                            f,
                            file_name=path.name,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        )
                else:
                    st.warning("No supervisor allocation found. Run Supervisor Allocation first.")

            if st.button("Generate AI Processing Report"):
                path = generate_ai_processing_report(
                    nl_config=nl_config,
                    seating_status=seating_result.status,
                    seating_runtime=seating_result.runtime_seconds,
                    rooms_used=seating_result.rooms_used,
                    students_assigned=seating_result.students_assigned,
                    verification_passed=(
                        verification_report.overall_passed if verification_report else None
                    ),
                    session_name=session_name,
                )
                st.success(f"Created: {path.name}")
                with open(path, "rb") as f:
                    st.download_button(
                        "Download AI Processing Report (Excel)",
                        f,
                        file_name=path.name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )

with tab_history:
    st.subheader("Files in reports folder")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(REPORTS_DIR.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)

    if not files:
        st.info("No reports generated yet.")
    else:
        for f in files[:30]:
            col_a, col_b = st.columns([4, 1])
            col_a.write(f"📄 {f.name}")
            with open(f, "rb") as fh:
                col_b.download_button(
                    "Download",
                    fh,
                    file_name=f.name,
                    key=f"dl_{f.name}",
                )
