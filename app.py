"""
EXAMFLOW - Executive Examination Management Portal
Autonomous AI-Powered Seating & Invigilation Allotment System
"""

import importlib
import streamlit as st

import ui.theme
importlib.reload(ui.theme)
from ui.theme import apply_theme
from database.connection import init_db, get_db_session
from database import repository as repo

# Page configuration
st.set_page_config(
    page_title="EXAMFLOW | Executive Examination Portal",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply shared theme
apply_theme()

# Ensure database is initialized
init_db()


def main():
    # --------------------------------------------------
    # FETCH REAL-TIME DATA METRICS
    # --------------------------------------------------
    with get_db_session() as db:
        n_students = repo.count_students(db)
        n_classrooms = repo.count_classrooms(db)
        n_seats = repo.count_available_seats(db)
        n_supervisors = repo.count_supervisors(db)
        n_plans = repo.count_plans(db)

    # --------------------------------------------------
    # HERO HEADER
    # --------------------------------------------------
    st.markdown(
        """
        <div class="exam-hero">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:16px;">
                <div style="flex: 1; min-width: 320px;">
                    <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
                        <span style="font-size:32px;">🎓</span>
                        <h1 style="margin:0; font-size:32px; font-weight:800; letter-spacing:-0.5px;">EXAMFLOW</h1>
                        <span class="exam-pill exam-pill-success">🟢 AI Engine Ready</span>
                    </div>
                    <p style="margin:0 0 10px 0; font-size:16px; font-weight:600; color:var(--exam-text);">
                        Autonomous Examination Seating & Invigilation Allocation Portal
                    </p>
                    <p style="margin:0; font-size:13.5px; color:var(--exam-muted); max-width:850px; line-height:1.55;">
                        Plan conflict-free university and institutional exams with mathematical guarantees. 
                        Translate everyday English spacing rules into constraints, auto-clean messy student files, 
                        and optimize 600+ students across exam halls in seconds.
                    </p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------
    # LIVE RESOURCE PULSE (REAL-TIME METRICS)
    # --------------------------------------------------
    st.markdown("### 📊 Live Resource Pulse")
    st.caption("Live metrics synchronized directly from your examination database.")

    stat_col1, stat_col2, stat_col3, stat_col4, stat_col5 = st.columns(5)

    with stat_col1:
        with st.container(border=True):
            st.metric(
                label="Registered Students",
                value=n_students,
                help="Total verified student records ready for seating allocation.",
            )

    with stat_col2:
        with st.container(border=True):
            st.metric(
                label="Examination Halls",
                value=n_classrooms,
                help="Total registered classrooms and examination halls.",
            )

    with stat_col3:
        with st.container(border=True):
            st.metric(
                label="Usable Desks",
                value=n_seats,
                help="Total usable desks across all active examination halls.",
            )

    with stat_col4:
        with st.container(border=True):
            st.metric(
                label="Duty Supervisors",
                value=n_supervisors,
                help="Faculty and invigilators registered for examination duty.",
            )

    with stat_col5:
        with st.container(border=True):
            st.metric(
                label="Seating Plans",
                value=n_plans,
                help="Total completed and stored examination plans.",
            )

    st.write("")
    st.divider()

    # --------------------------------------------------
    # INTERACTIVE 5-STEP EXAMINATION WORKFLOW WIZARD
    # --------------------------------------------------
    st.markdown("### 🧭 Interactive Examination Workflow Wizard")
    st.markdown(
        "Follow this **5-step sequential pipeline** to prepare, optimize, and execute "
        "your examination seating and invigilator duties with zero conflicts."
    )

    step_cols = st.columns(5)

    # STEP 1
    with step_cols[0]:
        with st.container(border=True):
            st.markdown(
                '<div style="display:flex; justify-content:space-between; align-items:center;">'
                '<span class="exam-step-num">1</span>'
                + (
                    f'<span class="exam-pill exam-pill-success">✓ Ready ({n_students})</span>'
                    if n_students > 0
                    else '<span class="exam-pill exam-pill-neutral">Pending</span>'
                )
                + "</div>",
                unsafe_allow_html=True,
            )
            st.markdown("**👥 Onboard Data**")
            st.caption(
                "Upload student & faculty rosters. Use 1-Click Auto-Clean to repair duplicates and missing fields."
            )
            st.write("")
            st.page_link(
                "pages/2_Student_Management.py",
                label="Manage Data ➔",
                icon="👥",
                use_container_width=True,
            )

    # STEP 2
    with step_cols[1]:
        with st.container(border=True):
            st.markdown(
                '<div style="display:flex; justify-content:space-between; align-items:center;">'
                '<span class="exam-step-num">2</span>'
                + (
                    f'<span class="exam-pill exam-pill-success">✓ Ready ({n_classrooms})</span>'
                    if n_classrooms > 0
                    else '<span class="exam-pill exam-pill-neutral">Pending</span>'
                )
                + "</div>",
                unsafe_allow_html=True,
            )
            st.markdown("**🏫 Hall Layouts**")
            st.caption(
                "Define grid dimensions (rows × cols), mark broken desks, or auto-detect layouts from room photos."
            )
            st.write("")
            st.page_link(
                "pages/3_Classroom_Layout_Management.py",
                label="Setup Rooms ➔",
                icon="🏫",
                use_container_width=True,
            )

    # STEP 3
    with step_cols[2]:
        with st.container(border=True):
            st.markdown(
                '<div style="display:flex; justify-content:space-between; align-items:center;">'
                '<span class="exam-step-num">3</span>'
                '<span class="exam-pill exam-pill-info">AI Config</span>'
                "</div>",
                unsafe_allow_html=True,
            )
            st.markdown("**📝 Spacing Rules**")
            st.caption(
                "Specify anti-cheating policies in plain English: strict checkerboard or normal horizontal spacing."
            )
            st.write("")
            st.page_link(
                "pages/4_Natural_Language_Requirements.py",
                label="Set Rules ➔",
                icon="📝",
                use_container_width=True,
            )

    # STEP 4
    with step_cols[3]:
        with st.container(border=True):
            st.markdown(
                '<div style="display:flex; justify-content:space-between; align-items:center;">'
                '<span class="exam-step-num">4</span>'
                + (
                    f'<span class="exam-pill exam-pill-success">✓ {n_plans} Saved</span>'
                    if n_plans > 0
                    else '<span class="exam-pill exam-pill-info">Ready</span>'
                )
                + "</div>",
                unsafe_allow_html=True,
            )
            st.markdown("**🚀 Seating Plan**")
            st.caption(
                "Execute the CP-SAT engine with room decomposition. Seats 600+ students in ~4 seconds."
            )
            st.write("")
            st.page_link(
                "pages/5_Seating_Generation.py",
                label="Generate Plan ➔",
                icon="🪑",
                use_container_width=True,
            )

    # STEP 5
    with step_cols[4]:
        with st.container(border=True):
            st.markdown(
                '<div style="display:flex; justify-content:space-between; align-items:center;">'
                '<span class="exam-step-num">5</span>'
                '<span class="exam-pill exam-pill-info">Export</span>'
                "</div>",
                unsafe_allow_html=True,
            )
            st.markdown("**🗺️ Maps & Reports**")
            st.caption(
                "Inspect interactive room seating charts, supervisor duty rosters, and export official reports."
            )
            st.write("")
            st.page_link(
                "pages/6_Seating_Visualization.py",
                label="View Seating ➔",
                icon="🗺️",
                use_container_width=True,
            )

    st.write("")
    st.divider()

    # --------------------------------------------------
    # SYSTEM READINESS & CAPACITY ASSESSMENT
    # --------------------------------------------------
    diag_col, cap_col = st.columns([1, 1])

    with diag_col:
        with st.container(border=True):
            st.subheader("⚡ System Readiness Assessment")

            if n_students > 0 and n_seats > 0:
                ratio = round(n_seats / n_students, 2)
                if ratio >= 1.5:
                    st.success(
                        f"**🟢 Optimum Seating Capacity:** You have **{n_seats} usable desks** for **{n_students} students** "
                        f"({ratio}× capacity margin). Ample space to enforce strict checkerboard spacing without bottlenecks."
                    )
                elif ratio >= 1.0:
                    st.info(
                        f"**🟡 Moderate Capacity:** You have **{n_seats} desks** for **{n_students} students** "
                        f"({ratio}× margin). Sufficient for single-seat alternate spacing."
                    )
                else:
                    st.warning(
                        f"**🔴 Capacity Shortage:** Registered students ({n_students}) exceed usable desks ({n_seats}). "
                        f"Please add more classrooms or activate closed rooms in Hall Management."
                    )
            else:
                st.info(
                    "Import student rosters and register classroom layouts to evaluate seating capacity."
                )

            st.write("")
            st.page_link(
                "pages/1_Dashboard.py",
                label="Open AI Copilot & Live Diagnostic Dashboard ➔",
                icon="🤖",
                use_container_width=True,
            )

    with cap_col:
        with st.container(border=True):
            st.subheader("🛡️ Enterprise Exam Assurance")
            st.markdown(
                """
                - 🛠️ **1-Click Auto-Clean & Repair:** Automatically fixes missing student names, deduplicates IDs, and infers batches.
                - 🧠 **Natural Language Rule Engine:** Turns plain everyday instructions into mathematical constraints.
                - ⚡ **Room-Decomposed CP-SAT Solver:** Solves complex multi-hall allocations in **~4 seconds**.
                - 🔬 **Independent Rules Checker:** 100% formal verification of adjacency and seating validity.
                """
            )
            st.write("")
            st.page_link(
                "pages/9_Reports_History.py",
                label="Browse Reports & Download Rosters ➔",
                icon="📄",
                use_container_width=True,
            )

    st.write("")
    st.caption("EXAMFLOW · Autonomous Examination Seating & Supervisor Allotment System")


if __name__ == "__main__":
    main()
