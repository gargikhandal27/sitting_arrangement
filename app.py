"""
Main entry point – Multimodal AI Examination Seating Arrangement System
Phase 2: Navigation & professional UI skeleton
"""
import streamlit as st

# Page configuration (must be first Streamlit command)
st.set_page_config(
    page_title="Exam Seating Allocation System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for cleaner look
st.markdown("""
<style>
    .main-header {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1f4e79;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.0rem;
        color: #555;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)


def main():
    st.markdown('<p class="main-header">🎓 Multimodal AI Examination Seating Arrangement System</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Computer Vision + Natural Language Processing + Constraint Optimization</p>', unsafe_allow_html=True)

    st.info(
        "**Project Complete (Phases 1–14)** – Navigation is ready. "
        "Use the sidebar to explore the pages. Real functionality will be added phase by phase."
    )

    # Quick overview cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="Registered Students", value="—", help="Will show real count after Phase 4")
    with col2:
        st.metric(label="Available Classrooms", value="—", help="Will show real count after Phase 5")
    with col3:
        st.metric(label="Usable Seats", value="—")
    with col4:
        st.metric(label="Available Supervisors", value="—")

    st.divider()

    st.subheader("System Overview")
    st.markdown("""
    This system combines three modalities:

    | Modality | Component | Purpose |
    |----------|-----------|---------|
    | **Structured Data** | CSV / Excel Import | Students, Classrooms, Supervisors |
    | **Images** | Computer Vision | Detect & confirm classroom seat layouts |
    | **Natural Language** | NLP Interpreter | Convert English instructions into constraints |

    All three feed into a **Constraint Optimization Engine** (Google OR-Tools CP-SAT) that generates seating plans and supervisor allocations.
    """)

    st.subheader("Development Roadmap")
    st.markdown("""
    - ✅ **Phase 1** – Project structure & virtual environment  
    - ✅ **Phase 2** – Streamlit navigation (current)  
    - ✅ **Phase 3** – Database models (SQLAlchemy)  
    - ✅ **Phase 4** – Structured data import & validation  
    - ✅ **Phase 5** – Classroom layout representation  
    - ✅ **Phase 6** – Computer Vision prototype  
    - ✅ **Phase 7** – Natural-language interpreter  
    - ✅ **Phase 8** – Seating optimization (OR-Tools)  
    - ✅ **Phase 9** – Supervisor allocation  
    - ✅ **Phase 10** – Independent verification  
    - ✅ **Phase 11** – Multimodal integration polish
    - ✅ **Phase 12** – Reports & history  
    """)

    st.success("Navigate using the **sidebar** on the left. Each page is ready for its future functionality.")


if __name__ == "__main__":
    main()
