"""
Seating Generation page (Phase 8)
"""
import streamlit as st
import pandas as pd

from database.connection import init_db, get_db_session
from services.allocation_service import run_seating_generation

st.title("🪑 Seating Generation")
st.markdown("Generate a seating plan using the OR-Tools CP-SAT solver.")

init_db()

# Pull confirmed NL config if available
nl_config = st.session_state.get("confirmed_nl_config", {})
default_adj = nl_config.get("adjacency_mode", "horizontal_vertical")
default_min = nl_config.get("minimize_classrooms", True)
default_time = nl_config.get("solver_time_limit_seconds", 60) or 60

st.subheader("Solver Settings")
col1, col2, col3 = st.columns(3)
with col1:
    adjacency_mode = st.selectbox(
        "Adjacency mode (batch separation)",
        options=["horizontal_vertical", "horizontal"],
        index=0 if default_adj == "horizontal_vertical" else 1,
    )
with col2:
    minimize_classrooms = st.checkbox("Minimize number of classrooms", value=bool(default_min))
with col3:
    time_limit = st.number_input("Time limit (seconds)", min_value=5, max_value=300, value=int(default_time))

if nl_config:
    st.info("Using settings previously confirmed from Natural Language Requirements.")

if st.button("Generate Seating Arrangement", type="primary"):
    with st.spinner("Running OR-Tools CP-SAT solver..."):
        with get_db_session() as db:
            result, layouts = run_seating_generation(
                db,
                adjacency_mode=adjacency_mode,
                minimize_classrooms=minimize_classrooms,
                time_limit_seconds=int(time_limit),
            )

    st.session_state["last_seating_result"] = result

    st.markdown("---")
    st.subheader("Solver Result")

    status_color = {
        "OPTIMAL": "green",
        "FEASIBLE": "blue",
        "INFEASIBLE": "red",
        "UNKNOWN": "orange",
        "MODEL_INVALID": "red",
    }.get(result.status, "gray")

    st.markdown(f"**Status:** :{status_color}[{result.status}]")
    st.write(result.message)
    st.write(f"**Runtime:** {result.runtime_seconds:.2f} seconds")
    st.write(f"**Students assigned:** {result.students_assigned}")
    st.write(f"**Rooms used:** {result.rooms_used}")

    if result.assignments:
        st.subheader("Assignments (first 50)")
        df = pd.DataFrame(result.assignments)
        st.dataframe(df.head(50), use_container_width=True)

        st.download_button(
            "Download full assignment CSV",
            df.to_csv(index=False).encode("utf-8"),
            file_name="seating_assignments.csv",
            mime="text/csv",
        )
    else:
        st.warning("No assignments produced.")
