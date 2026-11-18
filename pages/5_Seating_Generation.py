
"""
Seating Generation page (Phase 8)
"""
import streamlit as st
import pandas as pd

from ui.theme import apply_theme
from database.connection import init_db, get_db_session
from services.allocation_service import run_seating_generation


# --------------------------------------------------
# PAGE SETUP
# --------------------------------------------------

apply_theme()
init_db()

st.title("🪑 Seating Generation")

st.markdown(
    "Generate an examination seating plan using the "
    "OR-Tools CP-SAT optimization solver."
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

    minimize_classrooms = st.checkbox(
        "Minimize the number of classrooms",
        value=bool(default_min),
        help=(
            "Ask the solver to use as few classrooms as possible "
            "while satisfying the seating constraints."
        ),
    )


# --------------------------------------------------
# GENERATE SEATING ARRANGEMENT
# --------------------------------------------------

st.divider()

st.header("Generate Seating Plan")

st.markdown(
    "When you are ready, run the solver using the selected settings."
)

if st.button(
    "🚀 Generate Seating Arrangement",
    type="primary",
    use_container_width=True,
):

    try:
        with st.spinner(
            "Running OR-Tools CP-SAT solver. Please wait..."
        ):
            with get_db_session() as db:
                result, layouts = run_seating_generation(
                    db,
                    adjacency_mode=adjacency_mode,
                    minimize_classrooms=minimize_classrooms,
                    time_limit_seconds=int(time_limit),
                )

        # Save result for display after reruns.
        st.session_state["last_seating_result"] = result

        # Reset the result table view when a new plan is generated.
        st.session_state["seating_generation_completed"] = True

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
            "Review the solver status and examination constraints."
        )

else:

    # Initial state before the first generation.
    with st.container(border=True):
        st.info(
            "No seating plan has been generated in this session yet."
        )

        st.markdown(
            "1. Review the solver configuration.\n"
            "2. Select the required seating constraints.\n"
            "3. Click **Generate Seating Arrangement**.\n"
            "4. Review the solver results and download the assignments."
        )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "EXAMFLOW · Seating Generation · OR-Tools CP-SAT Solver"
)
