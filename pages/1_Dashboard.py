
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
from services.copilot_agent import handle_copilot_query, get_system_overview


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

# --------------------------------------------------
# EXAMFLOW AI ASSISTANT (INTEGRATED)
# --------------------------------------------------

st.divider()

st.subheader("🤖 ExamFlow AI Assistant")
st.caption(
    "Ask questions in plain English or click an action below to manage your examination logistics instantly."
)

if "copilot_messages" not in st.session_state:
    st.session_state["copilot_messages"] = [
        {
            "role": "assistant",
            "content": (
                "👋 Hello! I am your **ExamFlow Helper**.\n\n"
                "I can check if all students have desks, fix seating problems, or automatically create your complete exam seating plan.\n\n"
                "Ask a question below or choose an action!"
            ),
        }
    ]

# Quick action buttons
q_col1, q_col2, q_col3, q_col4 = st.columns(4)
dashboard_prompt = None

with q_col1:
    if st.button("📊 Overview", key="dash_overview", use_container_width=True):
        dashboard_prompt = "Show system overview"

with q_col2:
    if st.button("🔍 Check Space", key="dash_space", use_container_width=True):
        dashboard_prompt = "Run pre-flight feasibility check"

with q_col3:
    if st.button("🚀 Auto-Plan Exam", key="dash_autoplan", type="primary", use_container_width=True):
        dashboard_prompt = "Auto-plan exam with default settings"

with q_col4:
    if st.button("🗑️ Reset Chat", key="dash_reset", use_container_width=True):
        st.session_state["copilot_messages"] = [
            {
                "role": "assistant",
                "content": (
                    "👋 Conversation reset! Ask a question or click an action above to get started."
                ),
            }
        ]
        st.rerun()

# Chat messages display container
with st.container(border=True):
    chat_container = st.container(height=360)
    with chat_container:
        for msg in st.session_state["copilot_messages"]:
            avatar = "🤖" if msg["role"] == "assistant" else "👤"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

# Chat input
user_input = st.chat_input("Ask ExamFlow Assistant (e.g. 'Can we seat all students?', 'Auto-plan exam')...")
active_query = dashboard_prompt or user_input

if active_query:
    st.session_state["copilot_messages"].append({"role": "user", "content": active_query})

    with get_db_session() as db:
        resp = handle_copilot_query(active_query, db)

    st.session_state["copilot_messages"].append({"role": "assistant", "content": resp.message})

    if resp.status == "success":
        st.toast("✅ Action completed successfully!", icon="🎉")
    elif resp.status == "error":
        st.toast("⚠️ Notice: Could not complete action.", icon="⚠️")

    st.rerun()



# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "EXAMFLOW | AI-Based Examination Seating Arrangement "
    "and Supervisor Allotment System"
)
