"""
Supervisor Allocation page (Phase 9)
"""
import streamlit as st
import pandas as pd

from database.connection import init_db, get_db_session
from services.allocation_service import run_supervisor_allocation

st.title("🧑‍🏫 Supervisor Allocation")
st.markdown("Allocate supervisors to classrooms based on the latest seating plan.")

init_db()

# Need a seating result first
seating_result = st.session_state.get("last_seating_result")

if seating_result is None or not seating_result.assignments:
    st.warning(
        "No seating plan found in this session. "
        "Please run **Seating Generation** first."
    )
else:
    st.success(
        f"Using last seating plan: {seating_result.students_assigned} students "
        f"in {seating_result.rooms_used} room(s)  |  Status: {seating_result.status}"
    )

    nl_config = st.session_state.get("confirmed_nl_config", {})
    default_ratio = nl_config.get("students_per_supervisor", 30) or 30

    students_per_supervisor = st.number_input(
        "Students per supervisor",
        min_value=1,
        max_value=100,
        value=int(default_ratio),
        help="required_supervisors = ceil(students_in_room / this value)",
    )

    if st.button("Allocate Supervisors", type="primary"):
        with st.spinner("Allocating supervisors..."):
            with get_db_session() as db:
                result = run_supervisor_allocation(
                    db,
                    seating_assignments=seating_result.assignments,
                    students_per_supervisor=int(students_per_supervisor),
                )

        st.session_state["last_supervisor_result"] = result

        st.markdown("---")
        st.subheader("Allocation Result")

        if result.success:
            st.success(result.message)
        else:
            st.error(result.message)

        st.write(f"**Total required:** {result.total_required}")
        st.write(f"**Total assigned:** {result.total_assigned}")

        if result.assignments:
            st.subheader("Supervisor Assignments")
            df = pd.DataFrame(result.assignments)
            st.dataframe(df, use_container_width=True)

            st.download_button(
                "Download supervisor assignments CSV",
                df.to_csv(index=False).encode("utf-8"),
                file_name="supervisor_assignments.csv",
                mime="text/csv",
            )

        if result.shortages:
            st.subheader("Shortages")
            st.dataframe(pd.DataFrame(result.shortages), use_container_width=True)
