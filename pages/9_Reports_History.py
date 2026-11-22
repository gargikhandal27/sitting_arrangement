 
"""
Reports & History page (Phase 12)

Generate examination reports and browse previously
generated files.
"""

import re
import importlib
from datetime import datetime
from pathlib import Path

import streamlit as st

import ui.theme
importlib.reload(ui.theme)
from ui.theme import apply_theme
from database.connection import init_db, get_db_session
from services.classroom_layout_service import get_layout_summary
from services.reporting_service import (
    generate_student_seating_report,
    generate_supervisor_report,
    generate_classroom_report,
    generate_ai_processing_report,
)
from config import REPORTS_DIR


# --------------------------------------------------
# PAGE SETUP
# --------------------------------------------------

apply_theme()
init_db()

st.title("📄 Reports & History")

st.markdown(
    "Generate, download, and manage examination reports "
    "for the latest seating arrangement."
)

st.divider()

EXCEL_MIME = (
    "application/vnd.openxmlformats-officedocument."
    "spreadsheetml.sheet"
)


# --------------------------------------------------
# LOAD SESSION DATA
# --------------------------------------------------

seating_result = st.session_state.get(
    "last_seating_result"
)

supervisor_result = st.session_state.get(
    "last_supervisor_result"
)

verification_report = st.session_state.get(
    "last_verification_report"
)

nl_config = st.session_state.get(
    "confirmed_nl_config",
    {}
)

has_seating_plan = (
    seating_result is not None
    and bool(getattr(seating_result, "assignments", None))
)

has_supervisor_plan = (
    supervisor_result is not None
    and bool(getattr(supervisor_result, "assignments", None))
)

REPORTS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# --------------------------------------------------
# REPORT STATE HELPERS
# --------------------------------------------------

def save_generated_report(report_type, path):
    """Store the latest generated report path in session state."""

    st.session_state[
        f"examflow_report_{report_type}"
    ] = str(path)


def show_report_download(report_type, label):
    """Show a persistent download button if the file exists."""

    saved_path = st.session_state.get(
        f"examflow_report_{report_type}"
    )

    if not saved_path:
        return

    path = Path(saved_path)

    if not path.is_file():
        st.warning(
            "The previously generated report file "
            "is no longer available."
        )
        return

    st.download_button(
        label,
        data=path.read_bytes(),
        file_name=path.name,
        mime=EXCEL_MIME,
        key=f"download_{report_type}",
        use_container_width=True,
    )


def generate_report_safely(report_type, generator):
    """Run a report generator and display its result."""

    try:

        with st.spinner("Generating report..."):
            path = Path(generator())

        if not path.is_file():
            st.error(
                "The report generator did not create a valid file."
            )
            return

        save_generated_report(
            report_type,
            path,
        )

        st.success(
            f"Report generated successfully: {path.name}"
        )

    except Exception as error:

        st.error(
            f"Report generation failed: {error}"
        )


# --------------------------------------------------
# TABS
# --------------------------------------------------

tab_export, tab_history = st.tabs(
    [
        "📊 Generate Reports",
        "🕘 Report History",
    ]
)


# ==================================================
# TAB 1 — GENERATE REPORTS
# ==================================================

with tab_export:

    st.header("Report Generation")

    if not has_seating_plan:

        st.warning(
            "No seating plan is available."
        )

        st.info(
            "Generate a seating arrangement on Page 5 "
            "before creating examination reports."
        )

    else:

        # --------------------------------------------------
        # CURRENT PLAN SUMMARY
        # --------------------------------------------------

        st.subheader("Current Examination Plan")

        with st.container(border=True):

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
        # SESSION NAME
        # --------------------------------------------------

        st.divider()
        st.subheader("Report Settings")

        session_name = st.text_input(
            "Examination / Session Name",
            value="exam_session",
            help=(
                "This name will be included in "
                "generated report filenames."
            ),
        )

        # Keep filenames safe across operating systems.
        safe_session_name = re.sub(
            r"[^A-Za-z0-9_-]+",
            "_",
            session_name.strip(),
        ).strip("_")

        if not safe_session_name:
            safe_session_name = "exam_session"

        st.caption(
            f"Report filename prefix: {safe_session_name}"
        )

        # --------------------------------------------------
        # REPORT CARDS
        # --------------------------------------------------

        st.divider()
        st.header("Available Reports")

        col1, col2 = st.columns(2)

        # ----------------------------------------------
        # STUDENT SEATING REPORT
        # ----------------------------------------------

        with col1:

            with st.container(border=True):

                st.subheader("🪑 Student Seating Report")

                st.markdown(
                    "Export student seating assignments, "
                    "including classroom and seat information."
                )

                if st.button(
                    "Generate Student Seating Report",
                    type="primary",
                    use_container_width=True,
                    key="generate_student_report",
                ):

                    generate_report_safely(
                        "student",
                        lambda: generate_student_seating_report(
                            seating_result.assignments,
                            session_name=safe_session_name,
                        ),
                    )

                show_report_download(
                    "student",
                    "⬇️ Download Student Seating (Excel)",
                )

        # ----------------------------------------------
        # SUPERVISOR REPORT
        # ----------------------------------------------

        with col2:

            with st.container(border=True):

                st.subheader("🧑‍🏫 Supervisor Report")

                st.markdown(
                    "Export the supervisors assigned "
                    "to examination classrooms."
                )

                if not has_supervisor_plan:

                    st.warning(
                        "Supervisor allocation is not available."
                    )

                    st.caption(
                        "Run Page 7 to generate supervisor assignments."
                    )

                if st.button(
                    "Generate Supervisor Report",
                    use_container_width=True,
                    disabled=not has_supervisor_plan,
                    key="generate_supervisor_report",
                ):

                    generate_report_safely(
                        "supervisor",
                        lambda: generate_supervisor_report(
                            supervisor_result.assignments,
                            session_name=safe_session_name,
                        ),
                    )

                show_report_download(
                    "supervisor",
                    "⬇️ Download Supervisor Report (Excel)",
                )

        # ----------------------------------------------
        # CLASSROOM REPORT
        # ----------------------------------------------

        col3, col4 = st.columns(2)

        with col3:

            with st.container(border=True):

                st.subheader("🏫 Classroom Report")

                st.markdown(
                    "Export classroom layouts, capacities, "
                    "and student seating information."
                )

                if st.button(
                    "Generate Classroom Report",
                    use_container_width=True,
                    key="generate_classroom_report",
                ):

                    def create_classroom_report():

                        with get_db_session() as db:
                            summaries = get_layout_summary(db)

                        return generate_classroom_report(
                            summaries,
                            seating_result.assignments,
                            session_name=safe_session_name,
                        )

                    generate_report_safely(
                        "classroom",
                        create_classroom_report,
                    )

                show_report_download(
                    "classroom",
                    "⬇️ Download Classroom Report (Excel)",
                )

        # ----------------------------------------------
        # AI PROCESSING REPORT
        # ----------------------------------------------

        with col4:

            with st.container(border=True):

                st.subheader("🤖 AI Processing Report")

                st.markdown(
                    "Export processing information, solver "
                    "results, and verification status."
                )

                if st.button(
                    "Generate AI Processing Report",
                    use_container_width=True,
                    key="generate_ai_report",
                ):

                    generate_report_safely(
                        "ai",
                        lambda: generate_ai_processing_report(
                            nl_config=nl_config,
                            seating_status=seating_result.status,
                            seating_runtime=(
                                seating_result.runtime_seconds
                            ),
                            rooms_used=(
                                seating_result.rooms_used
                            ),
                            students_assigned=(
                                seating_result.students_assigned
                            ),
                            verification_passed=(
                                verification_report.overall_passed
                                if verification_report
                                else None
                            ),
                            session_name=safe_session_name,
                        ),
                    )

                show_report_download(
                    "ai",
                    "⬇️ Download AI Processing Report (Excel)",
                )


# ==================================================
# TAB 2 — REPORT HISTORY
# ==================================================

with tab_history:

    st.header("Generated Report History")

    st.markdown(
        "Browse and download files previously generated "
        "by the reporting system."
    )

    report_files = sorted(
        [
            path
            for path in REPORTS_DIR.iterdir()
            if path.is_file()
        ],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    # --------------------------------------------------
    # HISTORY SUMMARY
    # --------------------------------------------------

    with st.container(border=True):

        st.metric(
            "Available Report Files",
            len(report_files),
        )

    if not report_files:

        st.info(
            "No reports have been generated yet. "
            "Generated files will appear here."
        )

    else:

        search_text = st.text_input(
            "Search Reports",
            placeholder="Search by filename...",
            key="report_history_search",
        )

        filtered_files = [
            path
            for path in report_files
            if search_text.lower() in path.name.lower()
        ]

        st.caption(
            f"Showing {min(len(filtered_files), 30)} "
            f"of {len(filtered_files)} matching files."
        )

        if not filtered_files:

            st.warning(
                "No reports match your search."
            )

        else:

            for index, path in enumerate(
                filtered_files[:30]
            ):

                file_size_kb = (
                    path.stat().st_size / 1024
                )

                modified_time = datetime.fromtimestamp(
                    path.stat().st_mtime
                ).strftime("%d %b %Y, %I:%M %p")

                with st.container(border=True):

                    info_col, download_col = st.columns(
                        [3, 1]
                    )

                    with info_col:

                        st.markdown(
                            f"**📄 {path.name}**"
                        )

                        st.caption(
                            f"Size: {file_size_kb:.1f} KB"
                            f"  |  Generated/Modified: "
                            f"{modified_time}"
                        )

                    with download_col:

                        st.download_button(
                            "⬇️ Download",
                            data=path.read_bytes(),
                            file_name=path.name,
                            mime=EXCEL_MIME,
                            key=f"history_download_{index}",
                            use_container_width=True,
                        )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "EXAMFLOW · Reports & History"
)
