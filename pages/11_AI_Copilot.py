"""
AI Copilot & Central Orchestrator Page (Phase 1 AI Upgrade)
Provides an interactive conversational agent for managing examination logistics.
"""
import importlib
import streamlit as st
import streamlit.components.v1 as components

import ui.theme
importlib.reload(ui.theme)
from ui.theme import apply_theme

import services.copilot_agent
importlib.reload(services.copilot_agent)
from services.copilot_agent import handle_copilot_query, get_system_overview

from database.connection import init_db, get_db_session

apply_theme()
init_db()

# --------------------------------------------------
# INITIALIZE CHAT HISTORY
# --------------------------------------------------
if "copilot_messages" not in st.session_state:
    st.session_state["copilot_messages"] = [
        {
            "role": "assistant",
            "content": (
                "👋 Hello! I am your **ExamFlow AI Copilot**.\n\n"
                "I can analyze classroom capacities, diagnose seating bottlenecks, "
                "or autonomously coordinate the entire end-to-end exam allocation pipeline.\n\n"
                "Ask a question below or choose a quick action from the top bar or sidebar!"
            ),
        }
    ]

# --------------------------------------------------
# SIDEBAR ACTIONS
# --------------------------------------------------
prompt_from_button = None

with st.sidebar:
    st.markdown("### 🤖 Copilot Quick Actions")
    st.caption("Execute instant examination tasks:")

    if st.button("📊 System Overview", use_container_width=True):
        prompt_from_button = "Show system overview"

    if st.button("🔍 Check Feasibility", use_container_width=True):
        prompt_from_button = "Run pre-flight feasibility check"

    if st.button("👥 Registered Batches", use_container_width=True):
        prompt_from_button = "Show registered student batches"

    if st.button("🚀 Auto-Plan Exam", type="primary", use_container_width=True):
        prompt_from_button = "Auto-plan exam with default settings"

    st.markdown("---")
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state["copilot_messages"] = [
            {
                "role": "assistant",
                "content": (
                    "👋 Conversation reset! I am ready to help you with your examination logistics. "
                    "Ask a question or click an action from the top bar or sidebar."
                ),
            }
        ]
        st.rerun()


# --------------------------------------------------
# COMPACT HEADER & STATUS
# --------------------------------------------------
header_col1, header_col2 = st.columns([3, 1])
with header_col1:
    st.markdown("### 🤖 ExamFlow AI Copilot")

with header_col2:
    with get_db_session() as db:
        stats = get_system_overview(db)
        st.caption(f"**Live:** {stats['student_count']} students · {stats['total_usable_seats']} seats")

# Top quick action pill bar
pill_col1, pill_col2, pill_col3, pill_col4, pill_col5 = st.columns([1, 1, 1, 1.2, 0.8])
with pill_col1:
    if st.button("📊 Overview", key="pill_overview", use_container_width=True):
        prompt_from_button = "Show system overview"
with pill_col2:
    if st.button("🔍 Feasibility", key="pill_feasibility", use_container_width=True):
        prompt_from_button = "Run pre-flight feasibility check"
with pill_col3:
    if st.button("👥 Batches", key="pill_batches", use_container_width=True):
        prompt_from_button = "Show registered student batches"
with pill_col4:
    if st.button("⚡ Plan Now", key="pill_plan", type="primary", use_container_width=True):
        prompt_from_button = "Auto-plan exam with default settings"
with pill_col5:
    if st.button("🗑️ Reset", key="pill_reset", use_container_width=True):
        st.session_state["copilot_messages"] = [
            {
                "role": "assistant",
                "content": (
                    "👋 Conversation reset! I am ready to help you with your examination logistics."
                ),
            }
        ]
        st.rerun()

st.divider()

# Immediate toast feedback when quick action buttons are clicked
if prompt_from_button:
    if "Plan" in prompt_from_button or "plan" in prompt_from_button:
        st.toast("⚡ Running automated seating & supervisor solver... (~20s)", icon="⏳")
    elif "feasibility" in prompt_from_button.lower():
        st.toast("🔍 Checking seating & classroom feasibility...", icon="🧠")
    elif "overview" in prompt_from_button.lower():
        st.toast("📊 Loading live system overview...", icon="📋")
    elif "batch" in prompt_from_button.lower():
        st.toast("👥 Loading batch distributions...", icon="👥")

# --------------------------------------------------
# DISPLAY CHAT HISTORY
# --------------------------------------------------
for msg in st.session_state["copilot_messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# --------------------------------------------------
# HANDLE ACTIVE INPUT (From Button or Chat Input)
# --------------------------------------------------
user_text_input = st.chat_input("Ask ExamFlow Copilot (e.g., 'Can we seat all students?', 'Auto-plan exam')...")

active_prompt = prompt_from_button or user_text_input

if active_prompt:
    # 1. Render and append user message
    st.session_state["copilot_messages"].append({"role": "user", "content": active_prompt})
    with st.chat_message("user"):
        st.markdown(active_prompt)

    # 2. Process and render assistant response with live spinner
    with st.chat_message("assistant"):
        with st.spinner("🤖 Copilot is thinking & executing..."):
            with get_db_session() as db:
                try:
                    response = handle_copilot_query(active_prompt, db)
                    assistant_reply = response.message

                    if response.suggested_prompts:
                        assistant_reply += "\n\n---\n*Suggested next steps:*\n"
                        for sp in response.suggested_prompts:
                            assistant_reply += f"- *{sp}*\n"
                except Exception as ex:
                    assistant_reply = f"❌ **Error executing request**: {str(ex)}"

                st.markdown(assistant_reply)
                st.session_state["copilot_messages"].append(
                    {"role": "assistant", "content": assistant_reply}
                )

# Invisible bottom anchor right after messages
st.markdown('<div id="copilot-bottom-anchor" style="height: 1px; margin: 0; padding: 0;"></div>', unsafe_allow_html=True)

# Smooth auto-scroll script targeting section.main and bottom anchor
components.html(
    """
    <script>
        function autoScroll() {
            try {
                const doc = window.parent.document;
                const main = doc.querySelector('section.main') || doc.querySelector('[data-testid="stMain"]');
                if (main) {
                    main.scrollTo({ top: main.scrollHeight, behavior: 'smooth' });
                }
                const anchor = doc.getElementById('copilot-bottom-anchor');
                if (anchor) {
                    anchor.scrollIntoView({ behavior: 'smooth', block: 'end' });
                }
            } catch(e) {}
        }
        [30, 100, 250, 500, 900, 1600].forEach(function(t) {
            setTimeout(autoScroll, t);
        });
    </script>
    """,
    height=0,
)
