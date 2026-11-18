
"""
Natural-Language Requirements page (Phase 7)
"""
import streamlit as st
from ui.theme import apply_theme

apply_theme()

from services.natural_language_service import (
    interpret_instruction,
    config_to_human_summary,
)


# --------------------------------------------------
# PAGE HEADER
# --------------------------------------------------

st.title("💬 Natural Language Requirements")

st.markdown(
    "Describe your examination requirements in ordinary English. "
    "EXAMFLOW will identify supported settings and show you the "
    "configuration for review before applying it."
)

st.divider()


# --------------------------------------------------
# SUPPORTED REQUIREMENTS
# --------------------------------------------------

with st.expander("📘 What can you describe?", expanded=True):
    st.markdown("You can describe requirements such as:")

    examples = [
        "Arrange seating for 400 students.",
        "Students from the same batch must not sit horizontally or vertically adjacent.",
        "Use as few classrooms as possible.",
        "One supervisor per 30 students.",
        "Solver time limit 60 seconds.",
    ]

    for example in examples:
        st.markdown(f"- {example}")

    st.caption(
        "Only supported settings are extracted. Unsupported requirements "
        "are reported separately and are not applied."
    )


# --------------------------------------------------
# QUICK EXAMPLES
# --------------------------------------------------

st.subheader("Quick Examples")
st.caption("Choose an example to fill the instruction box.")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Example 1 · Full", use_container_width=True):
        st.session_state["nl_text"] = (
            "Arrange seating for 400 students from eight batches. "
            "Students from the same batch must not sit next to each other "
            "horizontally or vertically. "
            "Use as few classrooms as possible. "
            "Each classroom needs one supervisor per 30 students."
        )

with col2:
    if st.button("Example 2 · Simple", use_container_width=True):
        st.session_state["nl_text"] = (
            "Arrange 250 students. Same batch students should not sit "
            "horizontally adjacent. One supervisor per 25 students."
        )

with col3:
    if st.button("Example 3 · Minimal", use_container_width=True):
        st.session_state["nl_text"] = (
            "400 students. Minimize classrooms. "
            "Supervisor per 30 students."
        )


# --------------------------------------------------
# INSTRUCTION INPUT
# --------------------------------------------------

st.divider()
st.subheader("Examination Instructions")

instruction = st.text_area(
    "Enter your requirements",
    value=st.session_state.get("nl_text", ""),
    height=160,
    placeholder=(
        "Example: Arrange 400 students. Students from the same batch "
        "must not sit horizontally or vertically adjacent. "
        "Minimize classrooms. One supervisor per 30 students."
    ),
    help="Write your requirements in simple English.",
)

if st.button(
    "🔍 Interpret Instruction",
    type="primary",
    use_container_width=True,
):
    if not instruction.strip():
        st.warning("Please enter some instructions first.")
    else:
        result = interpret_instruction(instruction)
        st.session_state["nl_result"] = result
        st.session_state["nl_confirmed"] = False


# --------------------------------------------------
# INTERPRETATION RESULT
# --------------------------------------------------

if "nl_result" in st.session_state:
    result = st.session_state["nl_result"]

    st.divider()
    st.header("Interpretation Result")

    with st.container(border=True):
        st.markdown("**Your original instruction**")
        st.code(result.original_text, language=None)

    # Extracted settings
    st.subheader("Extracted Settings")

    if result.extracted_items:
        st.success("The following supported settings were identified:")

        for item in result.extracted_items:
            st.markdown(f"- {item}")
    else:
        st.warning("No supported settings could be extracted.")

    # Warnings
    if result.warnings:
        with st.container(border=True):
            st.warning("Warnings")

            for warning in result.warnings:
                st.markdown(f"- {warning}")

    # Unsupported requirements
    if result.unsupported:
        with st.container(border=True):
            st.error("Unsupported Requirements")

            st.caption(
                "These requirements were not applied because they "
                "are not currently supported."
            )

            for item in result.unsupported:
                st.markdown(f"- {item}")

    # Missing recommended parameters
    if result.missing:
        with st.container(border=True):
            st.info("Missing Recommended Parameters")

            for item in result.missing:
                st.markdown(f"- {item}")

    # Structured configuration
    st.divider()
    st.subheader("Structured Configuration")

    st.caption(
        "This is the configuration extracted by the system."
    )

    st.json(result.config.to_dict())

    # Human-readable summary
    st.subheader("Configuration Summary")

    with st.container(border=True):
        st.markdown(config_to_human_summary(result.config))


    # --------------------------------------------------
    # ADMINISTRATOR CONFIRMATION
    # --------------------------------------------------

    st.divider()
    st.header("Administrator Confirmation")

    st.info(
        "Please review the extracted settings and configuration "
        "before applying them."
    )

    st.checkbox(
        "I have reviewed the extracted settings and confirm they are correct.",
        key="nl_confirmed",
    )

    if st.session_state.get("nl_confirmed", False):

        if st.button(
            "✅ Apply Configuration",
            type="primary",
            use_container_width=True,
        ):
            # Store confirmed configuration for later phases
            st.session_state["confirmed_nl_config"] = (
                result.config.to_dict()
            )

            st.success(
                "Configuration confirmed and saved for the "
                "Seating Generation step."
            )

            st.balloons()

    else:
        st.caption(
            "Tick the confirmation checkbox to enable configuration application."
        )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "EXAMFLOW · Natural Language Requirements"
)
