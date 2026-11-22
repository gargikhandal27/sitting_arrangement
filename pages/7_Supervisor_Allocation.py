
"""
Supervisor Allocation page (Phase 9)
"""

import importlib
import streamlit as st
import pandas as pd

import ui.theme
importlib.reload(ui.theme)
from ui.theme import apply_theme
from database.connection import init_db, get_db_session
from services.allocation_service import run_supervisor_allocation


# --------------------------------------------------
# PAGE SETUP
# --------------------------------------------------

apply_theme()
init_db()

st.title("🧑‍🏫 Supervisor Allocation")

st.markdown(
    "Allocate examination supervisors to classrooms based on "
    "the latest generated seating plan."
)

st.divider()


# --------------------------------------------------
# CHECK FOR SEATING PLAN
# --------------------------------------------------

seating_result = st.session_state.get("last_seating_result")

if (
    seating_result is None
    or not getattr(seating_result, "assignments", None)
):

    st.warning(
        "No seating plan is available in this session."
    )

    st.info(
        "Please generate a seating arrangement on Page 5 "
        "before proceeding with supervisor allocation."
    )

else:

    # --------------------------------------------------
    # SEATING PLAN OVERVIEW
    # --------------------------------------------------

    st.header("Seating Plan Overview")

    with st.container(border=True):

        st.success(
            "A seating plan is available for supervisor allocation."
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
    # ALLOCATION SETTINGS
    # --------------------------------------------------

    st.divider()
    st.header("Allocation Settings")

    nl_config = st.session_state.get(
        "confirmed_nl_config",
        {},
    )

    default_ratio = (
        nl_config.get("students_per_supervisor", 30) or 30
    )

    default_ratio = max(
        1,
        min(100, int(default_ratio)),
    )

    with st.container(border=True):

        st.markdown("**Supervisor-to-Student Ratio**")

        students_per_supervisor = st.number_input(
            "Students per supervisor",
            min_value=1,
            max_value=100,
            value=default_ratio,
            step=1,
            help=(
                "Determines how many students one supervisor "
                "is responsible for. Required supervisors are "
                "calculated using the classroom student count."
            ),
        )

        st.caption(
            "Example: A classroom with 60 students requires "
            "2 supervisors when the ratio is 30 students per supervisor."
        )

        if nl_config.get("students_per_supervisor"):
            st.info(
                "The default ratio was loaded from your confirmed "
                "Natural Language Requirements."
            )

    # --------------------------------------------------
    # RUN ALLOCATION
    # --------------------------------------------------

    st.divider()
    st.header("Generate Supervisor Allocation")

    st.markdown(
        "Run the allocation process to assign available supervisors "
        "to the classrooms in your seating plan."
    )

    if st.button(
        "🧑‍🏫 Allocate Supervisors",
        type="primary",
        use_container_width=True,
    ):

        try:

            with st.spinner(
                "Allocating supervisors to classrooms..."
            ):

                with get_db_session() as db:

                    result = run_supervisor_allocation(
                        db,
                        seating_assignments=seating_result.assignments,
                        students_per_supervisor=int(
                            students_per_supervisor
                        ),
                    )

            st.session_state[
                "last_supervisor_result"
            ] = result

        except Exception as error:

            st.error(
                f"Supervisor allocation failed: {error}"
            )

    # --------------------------------------------------
    # DISPLAY ALLOCATION RESULT
    # --------------------------------------------------

    result = st.session_state.get(
        "last_supervisor_result"
    )

    if result is not None:

        st.divider()
        st.header("Allocation Results")

        if result.success:
            st.success(result.message)
        else:
            st.error(result.message)

        # Summary metrics
        with st.container(border=True):

            st.subheader("Allocation Summary")

            metric1, metric2 = st.columns(2)

            with metric1:
                st.metric(
                    "Supervisors Required",
                    result.total_required,
                )

            with metric2:
                st.metric(
                    "Supervisors Assigned",
                    result.total_assigned,
                )

            unassigned = max(
                0,
                result.total_required - result.total_assigned,
            )

            st.metric(
                "Unassigned Supervisors",
                unassigned,
            )

        # --------------------------------------------------
        # SUPERVISOR ASSIGNMENT TABLE
        # --------------------------------------------------

        if result.assignments:

            st.subheader("Supervisor Assignments")

            df = pd.DataFrame(result.assignments)

            st.caption(
                f"Total assignment records: {len(df)}"
            )

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
            )

            csv_data = df.to_csv(
                index=False
            ).encode("utf-8")

            st.download_button(
                "⬇️ Download Supervisor Assignments CSV",
                data=csv_data,
                file_name="supervisor_assignments.csv",
                mime="text/csv",
                use_container_width=True,
            )

        else:

            st.warning(
                "No supervisor assignments were produced."
            )

        # --------------------------------------------------
        # SHORTAGES
        # --------------------------------------------------

        if result.shortages:

            st.divider()
            st.subheader("Supervisor Shortages")

            st.warning(
                "Some classrooms may not have received "
                "the required number of supervisors."
            )

            shortage_df = pd.DataFrame(
                result.shortages
            )

            st.dataframe(
                shortage_df,
                use_container_width=True,
                hide_index=True,
            )

        else:

            if result.success:
                st.success(
                    "No supervisor shortages were reported."
                )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "EXAMFLOW · Supervisor Allocation"
)
