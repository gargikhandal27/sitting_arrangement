
"""
EXAMFLOW - Dashboard
Overview of examination management system status.
"""

import importlib
import streamlit as st

import ui.theme
importlib.reload(ui.theme)
from ui.theme import apply_theme
from database.connection import init_db, get_db_session
from database import repository as repo


# Apply shared application theme
apply_theme()


# --------------------------------------------------
# PAGE HEADER
# --------------------------------------------------

st.title("EXAMFLOW Dashboard")
st.markdown(
    "Monitor your examination resources and seating "
    "arrangement system from one place."
)

st.write("")


# --------------------------------------------------
# DATABASE STATUS
# --------------------------------------------------

database_ready = False

try:
    init_db()
    database_ready = True
    st.success("Database connected successfully. All tables are ready.")
except Exception as e:
    st.error(f"Database connection failed: {e}")


# --------------------------------------------------
# FETCH DASHBOARD STATISTICS
# --------------------------------------------------

n_students = 0
n_classrooms = 0
n_seats = 0
n_supervisors = 0
n_plans = 0

if database_ready:
    try:
        with get_db_session() as db:
            n_students = repo.count_students(db)
            n_classrooms = repo.count_classrooms(db)
            n_seats = repo.count_available_seats(db)
            n_supervisors = repo.count_supervisors(db)
            n_plans = repo.count_plans(db)

    except Exception as e:
        st.error(f"Could not retrieve dashboard statistics: {e}")


# --------------------------------------------------
# STATISTICS SECTION
# --------------------------------------------------

st.subheader("System Overview")
st.caption("A summary of your registered examination resources.")

st.write("")

stat1, stat2, stat3 = st.columns(3)

with stat1:
    with st.container(border=True):
        st.metric(
            label="Total Students",
            value=n_students,
            help="Number of registered students."
        )

with stat2:
    with st.container(border=True):
        st.metric(
            label="Classrooms",
            value=n_classrooms,
            help="Number of registered classrooms."
        )

with stat3:
    with st.container(border=True):
        st.metric(
            label="Usable Seats",
            value=n_seats,
            help="Total available classroom seats."
        )


stat4, stat5 = st.columns(2)

with stat4:
    with st.container(border=True):
        st.metric(
            label="Supervisors",
            value=n_supervisors,
            help="Number of registered supervisors."
        )

with stat5:
    with st.container(border=True):
        st.metric(
            label="Seating Plans",
            value=n_plans,
            help="Number of saved seating plans."
        )


# --------------------------------------------------
# RECENT EXAMINATION SESSIONS
# --------------------------------------------------

st.divider()

st.subheader("Recent Examination Sessions")

with st.container(border=True):
    st.markdown("**Examination Activity**")

    st.info(
        "No examination sessions are currently displayed. "
        "Import your data and generate seating plans to begin "
        "using the examination management workflow."
    )


# --------------------------------------------------
# QUICK ACTIONS
# --------------------------------------------------

st.divider()

st.subheader("Quick Actions")

st.caption(
    "Use these sections to manage examination data and "
    "prepare seating arrangements."
)

action1, action2 = st.columns(2)

with action1:
    with st.container(border=True):
        st.markdown("### Student & Data Management")
        st.write(
            "Import and manage students, classrooms, "
            "and examination supervisors."
        )
        st.page_link(
            "pages/2_Student_Management.py",
            label="Open Data Management",
            icon="👥"
        )

with action2:
    with st.container(border=True):
        st.markdown("### Classroom Layout")
        st.write(
            "Create and manage classroom layouts "
            "and seating configurations."
        )
        st.page_link(
            "pages/3_Classroom_Layout_Management.py",
            label="Manage Classrooms",
            icon="🏫"
        )

action3, action4 = st.columns(2)

with action3:
    with st.container(border=True):
        st.markdown("### Seating Requirements")
        st.write(
            "Define examination seating requirements "
            "using natural language."
        )
        st.page_link(
            "pages/4_Natural_Language_Requirements.py",
            label="Set Requirements",
            icon="📝"
        )

with action4:
    with st.container(border=True):
        st.markdown("### Generate Seating Plan")
        st.write(
            "Create examination seating arrangements "
            "using the allocation system."
        )
        st.page_link(
            "pages/5_Seating_Generation.py",
            label="Generate Seating",
            icon="🪑"
        )

with st.container(border=True):
    st.markdown("### 🤖 Autonomous AI Copilot & Diagnostics")
    st.write(
        "Chat with the AI Copilot to check seating feasibility, diagnose capacity bottlenecks, "
        "or orchestrate the entire examination allocation pipeline in one step."
    )
    st.page_link(
        "pages/11_AI_Copilot.py",
        label="Launch AI Copilot",
        icon="🤖"
    )



# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "EXAMFLOW | AI-Based Examination Seating Arrangement "
    "and Supervisor Allotment System"
)
