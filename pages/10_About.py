
"""
EXAMFLOW — About Page

Project overview, AI components, workflow,
technology stack, and design principles.
"""

import streamlit as st
from ui.theme import apply_theme


# --------------------------------------------------
# PAGE SETUP
# --------------------------------------------------

apply_theme()

st.title("ℹ️ About EXAMFLOW")

st.markdown(
    "Learn about the examination management system, "
    "its AI-powered features, and the technologies behind it."
)

st.divider()


# --------------------------------------------------
# PROJECT INTRODUCTION
# --------------------------------------------------

st.header("EXAMFLOW")

st.subheader(
    "Multimodal AI-Based Examination Seating Arrangement "
    "and Supervisor Allotment System"
)

st.markdown(
    """
    EXAMFLOW is an examination management application
    designed to help administrators organize student
    seating arrangements, manage classroom layouts,
    allocate supervisors, and verify examination plans.

    The system combines structured data processing,
    computer vision, natural language interpretation,
    and constraint optimization to support
    examination planning.
    """
)

with st.container(border=True):

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Project Type**")
        st.write("B.Tech Computer Science Engineering")

        st.markdown("**Academic Focus**")
        st.write("Artificial Intelligence")

    with col2:
        st.markdown("**Application**")
        st.write("Examination Management System")

        st.markdown("**Development Approach**")
        st.write("Modular, locally deployable application")


# --------------------------------------------------
# CORE FEATURES
# --------------------------------------------------

st.divider()
st.header("Core Features")

col1, col2 = st.columns(2)

with col1:

    with st.container(border=True):

        st.subheader("👨‍🎓 Student Management")

        st.write(
            "Import, validate, and manage student "
            "records used for seating allocation."
        )

    with st.container(border=True):

        st.subheader("🏫 Classroom Management")

        st.write(
            "Create classroom seating layouts manually "
            "or analyze classroom images using computer vision."
        )

    with st.container(border=True):

        st.subheader("🧠 Natural Language Requirements")

        st.write(
            "Convert administrator instructions into "
            "structured examination constraints."
        )

with col2:

    with st.container(border=True):

        st.subheader("🪑 Seating Generation")

        st.write(
            "Generate examination seating arrangements "
            "using constraint optimization."
        )

    with st.container(border=True):

        st.subheader("🧑‍🏫 Supervisor Allocation")

        st.write(
            "Assign supervisors to classrooms based "
            "on examination seating requirements."
        )

    with st.container(border=True):

        st.subheader("✅ Verification & Reporting")

        st.write(
            "Independently verify generated plans and "
            "export examination reports."
        )


# --------------------------------------------------
# AI COMPONENTS
# --------------------------------------------------

st.divider()
st.header("Artificial Intelligence Components")

st.markdown(
    "EXAMFLOW combines multiple AI and data-processing "
    "techniques within a single examination planning workflow."
)

ai_components = [
    {
        "component": "Structured Data Processing",
        "technology": "Pandas + Validation",
        "purpose": (
            "Clean and validate student, classroom, "
            "and supervisor records."
        ),
    },
    {
        "component": "Computer Vision",
        "technology": "OpenCV",
        "purpose": (
            "Analyze classroom images and help "
            "extract seating layouts."
        ),
    },
    {
        "component": "Natural Language Processing",
        "technology": "Controlled Instruction Parser",
        "purpose": (
            "Interpret administrator instructions "
            "as structured configuration."
        ),
    },
    {
        "component": "Constraint Optimization",
        "technology": "Google OR-Tools CP-SAT",
        "purpose": (
            "Generate seating arrangements "
            "subject to examination constraints."
        ),
    },
    {
        "component": "Independent Verification",
        "technology": "Rule-Based Verification Engine",
        "purpose": (
            "Check generated plans against "
            "hard constraints independently."
        ),
    },
]

for component in ai_components:

    with st.container(border=True):

        st.markdown(
            f"**{component['component']}**"
        )

        st.caption(
            f"Technology: {component['technology']}"
        )

        st.write(
            component["purpose"]
        )


# --------------------------------------------------
# TECHNOLOGY STACK
# --------------------------------------------------

st.divider()
st.header("Technology Stack")

technology_stack = {
    "Frontend": "Streamlit",
    "Programming Language": "Python",
    "Data Processing": "Pandas",
    "Computer Vision": "OpenCV",
    "Constraint Solver": "Google OR-Tools CP-SAT",
    "Data Storage": "Local Database",
    "Report Generation": "Excel and JSON",
}

with st.container(border=True):

    for technology, implementation in technology_stack.items():

        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown(
                f"**{technology}**"
            )

        with col2:
            st.write(
                implementation
            )


# --------------------------------------------------
# SYSTEM WORKFLOW
# --------------------------------------------------

st.divider()
st.header("EXAMFLOW Workflow")

st.markdown(
    "The examination planning process follows "
    "a structured sequence."
)

workflow_steps = [
    (
        "1. Student Data",
        "Import and validate student information.",
    ),
    (
        "2. Classroom Layout",
        "Configure available examination rooms and seats.",
    ),
    (
        "3. Requirements",
        "Define and confirm examination constraints.",
    ),
    (
        "4. Seating Generation",
        "Generate a seating plan using the optimization solver.",
    ),
    (
        "5. Seating Visualization",
        "Inspect the generated classroom seating charts.",
    ),
    (
        "6. Supervisor Allocation",
        "Assign supervisors to examination rooms.",
    ),
    (
        "7. Independent Verification",
        "Check the generated plan against hard constraints.",
    ),
    (
        "8. Reports",
        "Generate and download examination reports.",
    ),
]

for step_name, description in workflow_steps:

    with st.expander(step_name):

        st.write(description)


# --------------------------------------------------
# DESIGN PRINCIPLES
# --------------------------------------------------

st.divider()
st.header("Design Principles")

st.markdown(
    """
    EXAMFLOW is designed around the following principles:

    - **Local-first operation:** No paid APIs or
      mandatory cloud services.

    - **Manual fallbacks:** Administrators can configure
      classroom layouts and requirements manually.

    - **Administrator confirmation:** AI-interpreted
      instructions and image-derived layouts can be
      reviewed before use.

    - **Constraint integrity:** Hard constraints are
      not silently relaxed.

    - **Independent verification:** Generated plans
      are checked separately from the solver.

    - **Modular architecture:** Frontend pages, services,
      database operations, and optimization logic
      remain separated.
    """
)


# --------------------------------------------------
# PROJECT STATUS
# --------------------------------------------------

st.divider()
st.header("Project Development Status")

with st.container(border=True):

    st.success(
        "Frontend redesign completed across all 10 pages."
    )

    st.progress(1.0)

    st.markdown(
        "**Frontend Development:** 10 / 10 pages"
    )

    st.markdown(
        "**Next Stage:** End-to-end integration testing"
    )

    st.caption(
        "Functional testing of the complete workflow "
        "is still pending."
    )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.markdown(
    "**EXAMFLOW — Examination Management System**"
)

st.caption(
    "B.Tech Computer Science Engineering · "
    "Artificial Intelligence Course Project"
)
