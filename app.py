
"""
EXAMFLOW - Main entry point
Examination Management System
"""

import importlib
import streamlit as st
import ui.theme
importlib.reload(ui.theme)
from ui.theme import apply_theme

# Page configuration must be the first Streamlit command
st.set_page_config(
    page_title="EXAMFLOW | Examination Management System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Apply shared theme
apply_theme()

def main():

    st.markdown(
        '<p class="main-header">🎓 EXAMFLOW</p>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<p class="sub-header">Examination Management System</p>',
        unsafe_allow_html=True,
    )

    st.info(
        "**Welcome to EXAMFLOW!** Manage students, classrooms, "
        "exam seating plans, and teacher duty assignments all in one place."
    )

    # Dashboard metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Registered Students", "—")

    with col2:
        st.metric("Available Classrooms", "—")

    with col3:
        st.metric("Usable Desks", "—")

    with col4:
        st.metric("Available Teachers", "—")

    st.divider()

    st.subheader("How It Works")

    st.markdown("""
    EXAMFLOW brings together:

    | Input | Feature | What It Does |
    |---|---|---|
    | **Spreadsheets** | CSV / Excel Import | Student, classroom, and teacher lists |
    | **Room Photos** | Desk Detection | Checks desk layout from classroom images |
    | **Plain English** | Smart Instructions | Understands everyday requests (like *"skip one seat between students"*) |

    All of these feed into an **Automatic Seating Planner** that assigns fair, conflict-free seats and teacher duties in seconds.
    """)

    st.subheader("System Features")

    st.markdown("""
    - ✅ **Phase 1** – Project structure and clean setup
    - ✅ **Phase 2** – Easy sidebar navigation
    - ✅ **Phase 3** – Database storage
    - ✅ **Phase 4** – Simple spreadsheet import
    - ✅ **Phase 5** – Classroom layout management
    - ✅ **Phase 6** – Classroom desk photo detection
    - ✅ **Phase 7** – Plain English instruction reader
    - ✅ **Phase 8** – Fast automatic seating generator
    - ✅ **Phase 9** – Teacher duty assignment
    - ✅ **Phase 10** – Independent rules checker
    - ✅ **Phase 11** – Modern clean visual design
    - ✅ **Phase 12** – Downloadable reports & history
    - ✅ **Phase 13** – Smart Seating Problem Solver & Easy Fixes (Agent 2)
    - ✅ **Phase 14** – Helpful AI Assistant & Auto-Planner (Agent 1)
    """)

    st.success(
        "Navigate using the sidebar on the left to explore EXAMFLOW."
    )


if __name__ == "__main__":
    main()
