"""
Natural-Language Requirements page (Phase 7)
"""
import streamlit as st
import json

from services.natural_language_service import (
    interpret_instruction,
    config_to_human_summary,
)

st.title("💬 Natural Language Requirements")
st.markdown(
    "Describe examination constraints in ordinary English. "
    "The system extracts only supported settings and asks for your confirmation."
)

st.info(
    "Supported examples:\n"
    "- \"Arrange seating for 400 students\"\n"
    "- \"Students from the same batch must not sit horizontally or vertically adjacent\"\n"
    "- \"Use as few classrooms as possible\"\n"
    "- \"One supervisor per 30 students\"\n"
    "- \"Solver time limit 60 seconds\""
)

# Example buttons
st.markdown("**Quick examples** (click to fill):")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Example 1 – Full"):
        st.session_state["nl_text"] = (
            "Arrange seating for 400 students from eight batches. "
            "Students from the same batch must not sit next to each other horizontally or vertically. "
            "Use as few classrooms as possible. "
            "Each classroom needs one supervisor per 30 students."
        )
with col2:
    if st.button("Example 2 – Simple"):
        st.session_state["nl_text"] = (
            "Arrange 250 students. Same batch students should not sit horizontally adjacent. "
            "One supervisor per 25 students."
        )
with col3:
    if st.button("Example 3 – Minimal"):
        st.session_state["nl_text"] = "400 students. Minimize classrooms. Supervisor per 30 students."

# Text input
default_text = st.session_state.get("nl_text", "")
instruction = st.text_area(
    "Examination instructions",
    value=default_text,
    height=150,
    placeholder='Example: "Arrange 400 students. Same batch must not sit horizontally or vertically adjacent. Minimize classrooms. One supervisor per 30 students."',
)

if st.button("Interpret Instruction", type="primary"):
    if not instruction.strip():
        st.warning("Please enter some instructions first.")
    else:
        result = interpret_instruction(instruction)
        st.session_state["nl_result"] = result

# Show interpretation result
if "nl_result" in st.session_state:
    result = st.session_state["nl_result"]

    st.markdown("---")
    st.subheader("Interpretation Result")

    st.markdown("**Original instruction:**")
    st.code(result.original_text, language=None)

    if result.extracted_items:
        st.success("Extracted settings:")
        for item in result.extracted_items:
            st.write(f"- {item}")
    else:
        st.warning("No supported settings could be extracted.")

    if result.warnings:
        st.warning("Warnings:")
        for w in result.warnings:
            st.write(f"- {w}")

    if result.unsupported:
        st.error("Unsupported requirements (ignored):")
        for u in result.unsupported:
            st.write(f"- {u}")

    if result.missing:
        st.info("Missing recommended parameters:")
        for m in result.missing:
            st.write(f"- {m}")

    st.markdown("### Structured Configuration")
    st.json(result.config.to_dict())

    st.markdown("### Human-readable summary")
    st.markdown(config_to_human_summary(result.config))

    st.markdown("---")
    st.subheader("Administrator Confirmation")

    st.checkbox(
        "I have reviewed the extracted settings and confirm they are correct",
        key="nl_confirmed",
    )

    if st.session_state.get("nl_confirmed"):
        if st.button("Apply Configuration", type="primary"):
            # Store confirmed config in session state for later phases
            st.session_state["confirmed_nl_config"] = result.config.to_dict()
            st.success(
                "Configuration confirmed and saved for the seating generation step. "
                "You can now proceed to Seating Generation when ready."
            )
            st.balloons()
    else:
        st.caption("Please tick the confirmation box before applying the configuration.")
