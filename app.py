
"""
EXAMFLOW - Main entry point
Examination Management System
"""

import streamlit as st
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
        "examination seating arrangements, supervisor allocation, "
        "and verification from one place."
    )

    # Dashboard metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Registered Students", "—")

    with col2:
        st.metric("Available Classrooms", "—")

    with col3:
        st.metric("Usable Seats", "—")

    with col4:
        st.metric("Available Supervisors", "—")

    st.divider()

    st.subheader("System Overview")

    st.markdown("""
    This system combines three modalities:

    | Modality | Component | Purpose |
    |---|---|---|
    | **Structured Data** | CSV / Excel Import | Students, Classrooms, Supervisors |
    | **Images** | Computer Vision | Detect and confirm classroom seat layouts |
    | **Natural Language** | NLP Interpreter | Convert English instructions into constraints |

    All three feed into a **Constraint Optimization Engine**
    (Google OR-Tools CP-SAT) that generates seating plans
    and supervisor allocations.
    """)

    st.subheader("Development Roadmap")

    st.markdown("""
    - ✅ **Phase 1** – Project structure and virtual environment
    - ✅ **Phase 2** – Streamlit navigation
    - ✅ **Phase 3** – Database models (SQLAlchemy)
    - ✅ **Phase 4** – Structured data import and validation
    - ✅ **Phase 5** – Classroom layout representation
    - ✅ **Phase 6** – Computer Vision prototype
    - ✅ **Phase 7** – Natural-language interpreter
    - ✅ **Phase 8** – Seating optimization (OR-Tools)
    - ✅ **Phase 9** – Supervisor allocation
    - ✅ **Phase 10** – Independent verification
    - ✅ **Phase 11** – Multimodal integration polish
    - ✅ **Phase 12** – Reports and history
    """)

    st.success(
        "Navigate using the sidebar on the left to explore EXAMFLOW."
    )


if __name__ == "__main__":
    main()
