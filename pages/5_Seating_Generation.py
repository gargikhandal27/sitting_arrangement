"""
Seating Generation page (Phase 8 + AI Infeasibility Agent)
"""
import importlib
import streamlit as st
import pandas as pd

import ui.theme
importlib.reload(ui.theme)
from ui.theme import apply_theme
from database.connection import init_db, get_db_session
from services.allocation_service import run_seating_generation, load_students_for_solver, load_supervisors_for_solver
from services.classroom_layout_service import get_all_layouts
from services.infeasibility_agent import diagnose_seating_feasibility


# --------------------------------------------------
# PAGE SETUP
# --------------------------------------------------

apply_theme()
init_db()

st.title("🪑 Seating Generation")

st.markdown(
    "Generate an examination seating plan using the "
    "OR-Tools CP-SAT optimization solver with **AI Infeasibility Diagnostics**."
)

st.divider()


# --------------------------------------------------
# LOAD CONFIRMED NATURAL LANGUAGE SETTINGS
# --------------------------------------------------

nl_config = st.session_state.get("confirmed_nl_config", {})

default_adj = nl_config.get(
    "adjacency_mode",
    "horizontal_vertical",
)

default_min = nl_config.get(
    "minimize_classrooms",
    True,
)

default_time = nl_config.get(
    "solver_time_limit_seconds",
    60,
) or 60

# Keep the number input within its permitted range.
default_time = max(5, min(300, int(default_time)))


# --------------------------------------------------
# SOLVER SETTINGS
# --------------------------------------------------

st.header("Solver Configuration")

if nl_config:
    st.info(
        "Settings confirmed on the Natural Language Requirements "
        "page are being used as the default values below. "
        "You can review or change them before generating."
    )
else:
    st.caption(
        "Configure the seating constraints before running the solver."
    )

with st.container(border=True):

    col1, col2 = st.columns(2)

    with col1:
        adjacency_options = [
            "horizontal_vertical",
            "horizontal",
        ]

        adjacency_mode = st.selectbox(
            "Batch separation rule",
            options=adjacency_options,
            index=(
                0
                if default_adj == "horizontal_vertical"
                else 1
            ),
            format_func=lambda value: {
                "horizontal_vertical": (
                    "Horizontal and Vertical"
                ),
                "horizontal": "Horizontal Only",
            }[value],
            help=(
                "Controls which neighboring seats are checked "
                "when separating students from the same batch."
            ),
        )

    with col2:
        time_limit = st.number_input(
            "Solver time limit (seconds)",
            min_value=5,
            max_value=300,
            value=default_time,
            step=5,
            help=(
                "Maximum time allowed for the solver. "
                "A longer limit may allow it to find a better solution."
            ),
        )

    # Classroom selection filter
    with get_db_session() as db:
        all_db_layouts = get_all_layouts(db)

    active_room_options = [
        f"{lay.room_id} ({lay.usable_seats} seats)"
        for lay in all_db_layouts if lay.is_available and lay.usable_seats > 0
    ]
    room_id_map = {
        f"{lay.room_id} ({lay.usable_seats} seats)": lay.room_id
        for lay in all_db_layouts if lay.is_available and lay.usable_seats > 0
    }

    selected_room_labels = st.multiselect(
        "Classrooms to include in this examination",
        options=active_room_options,
        default=active_room_options,
        help="Select which classrooms to include. Deselect rooms to test capacity shortages or restrict exams to specific halls."
    )
    selected_room_ids = [room_id_map[lbl] for lbl in selected_room_labels]

    minimize_classrooms = st.checkbox(
        "Minimize the number of classrooms",
        value=bool(default_min),
        help=(
            "Ask the solver to use as few classrooms as possible "
            "while satisfying the seating constraints."
        ),
    )


# --------------------------------------------------
# PRE-FLIGHT FEASIBILITY & GENERATE BUTTONS
# --------------------------------------------------

st.divider()

st.header("Generate Seating Plan")

st.markdown(
    "You can run an **AI Pre-flight Feasibility Check** to mathematically test whether "
    "a solution exists before launching the solver."
)

btn_col1, btn_col2 = st.columns([1, 1])

with btn_col1:
    run_preflight = st.button(
        "🤖 AI Pre-flight Feasibility Check",
        use_container_width=True,
        help="Checks bipartite graph capacity and batch bounds without running the full solver.",
    )

with btn_col2:
    run_solver = st.button(
        "🚀 Generate Seating Arrangement",
        type="primary",
        use_container_width=True,
    )

# Pre-flight check execution
if run_preflight:
    with get_db_session() as db:
        students = load_students_for_solver(db)
        layouts = get_all_layouts(db)
        if selected_room_ids is not None:
            layouts = [lay for lay in layouts if lay.room_id in selected_room_ids]
        supervisors = load_supervisors_for_solver(db)

        diag_report = diagnose_seating_feasibility(
            students=students,
            layouts=layouts,
            adjacency_mode=adjacency_mode,
            time_limit_seconds=int(time_limit),
            supervisors=supervisors,
        )
        st.session_state["preflight_report"] = diag_report

# Display Pre-flight Report if available
if "preflight_report" in st.session_state:
    diag = st.session_state["preflight_report"]
    with st.container(border=True):
        st.subheader("🔍 AI Pre-Flight Feasibility Report")
        if diag.is_feasible:
            st.success(f"**Feasible**: {diag.summary}")
        else:
            st.warning(f"**Potential Infeasibility**: {diag.summary}")

        # Issues
        for issue in diag.issues:
            icon = "❌" if issue.severity == "error" else "⚠️"
            st.markdown(f"- **{icon} {issue.title}**: {issue.description}")

        # Remediations
        if diag.remediations:
            st.markdown("##### 💡 Suggested Actions:")
            for r in diag.remediations:
                st.markdown(f"• **{r.title}**: {r.description} *({r.impact})*")


# Seating solver execution
if run_solver:
    try:
        with st.spinner("Running OR-Tools CP-SAT solver. Please wait..."):
            with get_db_session() as db:
                result, layouts = run_seating_generation(
                    db,
                    adjacency_mode=adjacency_mode,
                    minimize_classrooms=minimize_classrooms,
                    time_limit_seconds=int(time_limit),
                    selected_room_ids=selected_room_ids,
                )

        # Save result for display after reruns.
        st.session_state["last_seating_result"] = result
        st.session_state["last_seating_layouts"] = layouts
        st.session_state["seating_generation_completed"] = True

        # Run diagnosis if not optimal/feasible
        if result.status not in ("OPTIMAL", "FEASIBLE"):
            with get_db_session() as db:
                students = load_students_for_solver(db)
                supervisors = load_supervisors_for_solver(db)
                diag = diagnose_seating_feasibility(
                    students=students,
                    layouts=layouts,
                    adjacency_mode=adjacency_mode,
                    time_limit_seconds=int(time_limit),
                    solver_result=result,
                    supervisors=supervisors,
                )
                st.session_state["infeasibility_diagnosis"] = diag
        else:
            st.session_state.pop("infeasibility_diagnosis", None)

    except Exception as error:
        st.error(
            f"An error occurred while generating the seating plan: {error}"
        )


# --------------------------------------------------
# DISPLAY SOLVER RESULT
# --------------------------------------------------

result = st.session_state.get("last_seating_result")

if result is not None:

    st.divider()
    st.header("Solver Results")

    status_colors = {
        "OPTIMAL": "🟢",
        "FEASIBLE": "🔵",
        "INFEASIBLE": "🔴",
        "UNKNOWN": "🟠",
        "MODEL_INVALID": "🔴",
    }

    status_icon = status_colors.get(
        result.status,
        "⚪",
    )

    with st.container(border=True):

        st.markdown("### Optimization Status")

        st.markdown(
            f"## {status_icon} {result.status}"
        )

        st.write(result.message)

        st.divider()

        metric1, metric2, metric3 = st.columns(3)

        with metric1:
            st.metric(
                "Students Assigned",
                result.students_assigned,
            )

        with metric2:
            st.metric(
                "Classrooms Used",
                result.rooms_used,
            )

        with metric3:
            st.metric(
                "Solver Runtime",
                f"{result.runtime_seconds:.2f} sec",
            )

    # --------------------------------------------------
    # AI INFEASIBILITY DIAGNOSTICS & REMEDIATION PANEL
    # --------------------------------------------------
    diag = st.session_state.get("infeasibility_diagnosis")
    if result.status not in ("OPTIMAL", "FEASIBLE") and diag is not None:

        st.divider()
        st.subheader("🤖 AI Infeasibility Diagnostic & Negotiation Agent")

        st.error(
            f"**Root Cause Diagnosis**: {diag.summary}"
        )

        # Issues details
        with st.expander("🔍 Detailed Root Cause Breakdown", expanded=True):
            for issue in diag.issues:
                st.markdown(f"#### ⚠️ {issue.title}")
                st.write(issue.description)

        # Batch density breakdown table if present
        if diag.batch_metrics:
            st.markdown("#### 📊 Batch Independent Capacity Breakdown")
            st.caption(
                "Shows the maximum number of seats a single batch can legally occupy across all active classrooms "
                "under the current separation rules vs actual student headcount."
            )
            batch_df = pd.DataFrame([
                {
                    "Batch": b.batch,
                    "Students": b.student_count,
                    "Max Safe Capacity": b.max_independent_capacity,
                    "Capacity Utilization": f"{b.utilization_pct}%",
                    "Status": "❌ Bottleneck" if b.is_bottleneck else "✅ Fits",
                }
                for b in diag.batch_metrics
            ])
            st.dataframe(batch_df, use_container_width=True, hide_index=True)

        # Interactive 1-Click Remediations
        if diag.remediations:
            st.subheader("💡 1-Click AI Remediation Proposals")
            st.markdown(
                "The AI Diagnostic Agent proposes the following automated trade-offs to achieve a feasible solution:"
            )

            for i, rem in enumerate(diag.remediations):
                with st.container(border=True):
                    rem_col1, rem_col2 = st.columns([3, 1])
                    with rem_col1:
                        st.markdown(f"**{rem.title}**")
                        st.caption(rem.description)
                        st.info(f"**Expected Impact**: {rem.impact}")

                    with rem_col2:
                        if rem.action_type == "relax_adjacency":
                            if st.button("⚡ Apply & Re-solve", key=f"rem_btn_{i}", type="primary"):
                                st.session_state["confirmed_nl_config"] = st.session_state.get("confirmed_nl_config", {})
                                st.session_state["confirmed_nl_config"]["adjacency_mode"] = rem.payload.get("target_adjacency", "horizontal")
                                st.rerun()

                        elif rem.action_type == "increase_time":
                            if st.button("⏱️ Increase & Re-solve", key=f"rem_btn_{i}", type="primary"):
                                st.session_state["confirmed_nl_config"] = st.session_state.get("confirmed_nl_config", {})
                                st.session_state["confirmed_nl_config"]["solver_time_limit_seconds"] = rem.payload.get("time_limit", 120)
                                st.rerun()

                        elif rem.action_type == "activate_room":
                            st.page_link(
                                "pages/3_Classroom_Layout_Management.py",
                                label="Go to Classrooms",
                                icon="🏫",
                            )

    # --------------------------------------------------
    # ASSIGNMENT TABLE
    # --------------------------------------------------

    if result.assignments:

        st.subheader("Generated Seat Assignments")

        df = pd.DataFrame(result.assignments)

        st.caption(
            f"Total assignment records: {len(df)}. "
            "The table below displays the first 50 records."
        )

        st.dataframe(
            df.head(50),
            use_container_width=True,
            hide_index=True,
        )

        # --------------------------------------------------
        # DOWNLOAD CSV
        # --------------------------------------------------

        st.divider()
        st.subheader("Export Seating Assignments")

        csv_data = df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            label="⬇️ Download Full Assignment CSV",
            data=csv_data,
            file_name="seating_assignments.csv",
            mime="text/csv",
            use_container_width=True,
        )

    else:
        st.warning(
            "No assignments were produced. "
            "Review the AI Infeasibility Diagnostic panel above for concrete remedies."
        )

else:

    # Initial state before the first generation.
    with st.container(border=True):
        st.info(
            "No seating plan has been generated in this session yet."
        )

        st.markdown(
            "1. Review the solver configuration.\n"
            "2. Run the **AI Pre-flight Feasibility Check** to detect any capacity or batch bottlenecks.\n"
            "3. Click **Generate Seating Arrangement**.\n"
            "4. Review the solver results or AI Diagnostic suggestions."
        )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "EXAMFLOW · Seating Generation · OR-Tools CP-SAT Solver with AI Infeasibility Diagnostics"
)
