
"""
EXAMFLOW - Classroom Layout Management
Manual layout creation, computer vision analysis,
seat visualization, and seat availability management.
"""

import streamlit as st
import pandas as pd
from pathlib import Path

from ui.theme import apply_theme

from database.connection import init_db, get_db_session

from services.classroom_layout_service import (
    create_manual_classroom,
    get_classroom_layout,
    set_seat_availability,
    confirm_layout,
    get_layout_summary,
    build_adjacency_list,
)

from services.image_analysis_service import (
    save_uploaded_image,
    analyze_classroom_image,
    detections_to_grid_proposal,
)


# ==================================================
# INITIALIZATION
# ==================================================

apply_theme()
init_db()


# ==================================================
# PAGE HEADER
# ==================================================

st.title("Classroom Layout Management")

st.markdown(
    "Design examination classrooms, analyse seating arrangements "
    "using computer vision, and manage individual seat availability."
)

st.write("")

st.info(
    "Create classroom layouts manually or use image analysis "
    "to estimate the seating arrangement. All image detections "
    "must be reviewed and confirmed by the administrator."
)


# ==================================================
# MANAGEMENT TABS
# ==================================================

tab_manual, tab_vision, tab_view, tab_edit = st.tabs(
    [
        "🏫 Create Manual Layout",
        "📷 Image Analysis",
        "🗺️ View Layouts",
        "✏️ Edit Seats",
    ]
)


# ==================================================
# TAB 1: CREATE MANUAL CLASSROOM
# ==================================================

with tab_manual:

    st.subheader("Create a New Classroom")

    st.caption(
        "Define the classroom dimensions and automatically "
        "generate a rectangular seating grid."
    )

    with st.container(border=True):

        st.markdown("### Classroom Details")

        with st.form("create_classroom_form"):

            col1, col2 = st.columns(2)

            with col1:

                room_id = st.text_input(
                    "Room ID *",
                    placeholder="Example: R101",
                )

                room_name = st.text_input(
                    "Room Name *",
                    placeholder="Example: Main Examination Hall",
                )

            with col2:

                rows = st.number_input(
                    "Number of Rows *",
                    min_value=1,
                    max_value=30,
                    value=5,
                    step=1,
                )

                columns = st.number_input(
                    "Number of Columns *",
                    min_value=1,
                    max_value=30,
                    value=6,
                    step=1,
                )

            is_available = st.checkbox(
                "Classroom is available",
                value=True,
            )

            st.divider()

            st.markdown("**Estimated Seating Capacity**")

            st.metric(
                "Total Seats",
                int(rows) * int(columns),
            )

            submitted = st.form_submit_button(
                "Create Classroom & Generate Seats",
                type="primary",
                use_container_width=True,
            )

            if submitted:

                if not room_id.strip() or not room_name.strip():

                    st.error(
                        "Please enter both Room ID and Room Name."
                    )

                else:

                    with get_db_session() as db:

                        success, message, cid = create_manual_classroom(
                            db,
                            room_id=room_id.strip(),
                            room_name=room_name.strip(),
                            rows=int(rows),
                            columns=int(columns),
                            is_available=is_available,
                        )

                    if success:

                        st.success(message)
                        st.balloons()

                    else:

                        st.error(message)


# ==================================================
# TAB 2: COMPUTER VISION IMAGE ANALYSIS
# ==================================================

with tab_vision:

    st.subheader("Classroom Image Analysis")

    st.caption(
        "Use computer vision to identify possible desks and seats "
        "from classroom photographs or floor plans."
    )

    with st.container(border=True):

        st.markdown("### How Image Analysis Works")

        st.markdown(
            """
            1. Upload a classroom photograph or floor plan.
            2. OpenCV detects rectangular regions that may represent desks or seats.
            3. Review the annotated image and detected regions.
            4. Use the estimated grid as a guide for creating a classroom layout.
            """
        )

        st.warning(
            "Computer vision detections are only suggestions. "
            "The administrator must confirm the final classroom layout."
        )

    st.write("")

    uploaded = st.file_uploader(
        "Upload Classroom Photograph or Floor Plan",
        type=["jpg", "jpeg", "png", "bmp", "webp"],
        key="cv_uploader",
        help="Supported formats: JPG, JPEG, PNG, BMP, WEBP.",
    )

    if uploaded is not None:

        st.markdown("### Uploaded Image")

        st.image(
            uploaded,
            caption="Original classroom image",
            use_container_width=True,
        )

        if st.button(
            "Run Image Analysis",
            type="primary",
            key="run_cv_analysis",
            use_container_width=True,
        ):

            with st.spinner(
                "Analysing classroom image using OpenCV..."
            ):

                try:

                    img_path = save_uploaded_image(uploaded)

                    result = analyze_classroom_image(img_path)

                    if not result.success:

                        st.error(result.message)

                        st.session_state.pop("cv_result", None)

                    else:

                        st.session_state["cv_result"] = result

                        st.success(result.message)

                except Exception as e:

                    st.error(f"Image analysis failed: {e}")

                    st.session_state.pop("cv_result", None)

        # Display saved analysis result.
        result = st.session_state.get("cv_result")

        if result is not None and result.success:

            st.divider()

            st.markdown("### Analysis Results")

            if (
                result.annotated_path
                and Path(result.annotated_path).exists()
            ):

                st.image(
                    result.annotated_path,
                    caption="Annotated detections",
                    use_container_width=True,
                )

            metric1, metric2, metric3 = st.columns(3)

            with metric1:

                st.metric(
                    "Detected Regions",
                    len(result.detections),
                )

            with metric2:

                st.metric(
                    "Image Width",
                    result.image_width,
                )

            with metric3:

                st.metric(
                    "Image Height",
                    result.image_height,
                )

            st.caption(f"Detection method: {result.method}")

            if result.detections:

                proposal = detections_to_grid_proposal(
                    result.detections,
                    result.image_width,
                    result.image_height,
                )

                st.markdown("### Estimated Seating Grid")

                estimate1, estimate2 = st.columns(2)

                with estimate1:

                    st.metric(
                        "Estimated Rows",
                        proposal["estimated_rows"],
                    )

                with estimate2:

                    st.metric(
                        "Estimated Columns",
                        proposal["estimated_columns"],
                    )

                st.info(
                    f"Grid estimate based on "
                    f"{proposal['num_detections']} detections."
                )

                st.caption(proposal["note"])

                detection_data = [
                    {
                        "Detection": i + 1,
                        "Center X": d.center_x,
                        "Center Y": d.center_y,
                        "Width": d.width,
                        "Height": d.height,
                        "Confidence": d.confidence,
                    }
                    for i, d in enumerate(result.detections)
                ]

                with st.expander("View Detection Details"):

                    st.dataframe(
                        pd.DataFrame(detection_data),
                        use_container_width=True,
                        hide_index=True,
                    )

            else:

                st.warning(
                    "No possible seating regions were detected. "
                    "You can still create a classroom manually."
                )

            # --------------------------------------
            # CREATE LAYOUT USING ANALYSIS
            # --------------------------------------

            st.divider()

            st.markdown("### Create Classroom from Analysis")

            st.caption(
                "Use the image analysis as a reference and "
                "enter the final classroom dimensions."
            )

            with st.form("cv_create_form"):

                cv_col1, cv_col2 = st.columns(2)

                with cv_col1:

                    cv_room_id = st.text_input(
                        "Room ID *",
                        value="R_CV_01",
                    )

                    cv_room_name = st.text_input(
                        "Room Name *",
                        value="Classroom from Image",
                    )

                with cv_col2:

                    cv_rows = st.number_input(
                        "Rows to Create",
                        min_value=1,
                        max_value=30,
                        value=5,
                        key="cv_rows",
                    )

                    cv_cols = st.number_input(
                        "Columns to Create",
                        min_value=1,
                        max_value=30,
                        value=6,
                        key="cv_cols",
                    )

                create_btn = st.form_submit_button(
                    "Create Classroom Layout",
                    type="primary",
                    use_container_width=True,
                )

                if create_btn:

                    if not cv_room_id.strip() or not cv_room_name.strip():

                        st.error(
                            "Room ID and Room Name are required."
                        )

                    else:

                        with get_db_session() as db:

                            success, message, cid = create_manual_classroom(
                                db,
                                room_id=cv_room_id.strip(),
                                room_name=cv_room_name.strip(),
                                rows=int(cv_rows),
                                columns=int(cv_cols),
                                is_available=True,
                            )

                        if success:

                            st.success(
                                message
                                + " You can now edit individual seats "
                                "in the Edit Seats tab."
                            )

                            st.balloons()

                        else:

                            st.error(message)


# ==================================================
# TAB 3: VIEW CLASSROOM LAYOUTS
# ==================================================

with tab_view:

    st.subheader("Classroom Layout Overview")

    st.caption(
        "Explore registered classrooms and preview their seating grids."
    )

    with get_db_session() as db:

        summaries = get_layout_summary(db)

    if not summaries:

        st.info(
            "No classroom layouts are available yet. "
            "Create a classroom using the Manual Layout or "
            "Image Analysis tab."
        )

    else:

        st.markdown("### Registered Classrooms")

        st.dataframe(
            pd.DataFrame(summaries),
            use_container_width=True,
            hide_index=True,
        )

        st.divider()

        st.markdown("### Seat Grid Preview")

        room_options = {
            f"{s['room_id']} - {s['room_name']}": s["classroom_id"]
            for s in summaries
        }

        selected_label = st.selectbox(
            "Select Classroom",
            list(room_options.keys()),
            key="view_select",
        )

        if selected_label:

            cid = room_options[selected_label]

            with get_db_session() as db:

                layout = get_classroom_layout(db, cid)

            if layout and layout.rows and layout.columns:

                st.write(
                    f"**{layout.room_id}** | "
                    f"{layout.usable_seats} usable seats / "
                    f"{layout.total_seats} total seats"
                )

                st.caption(
                    f"Layout source: {layout.layout_source}"
                )

                grid = {
                    (seat.row, seat.col): seat
                    for seat in layout.seats
                    if seat.row and seat.col
                }

                # Build seat grid.
                html = """
                <div style="
                    overflow-x:auto;
                    padding:12px;
                    background:rgba(40,120,200,0.04);
                    border-radius:12px;
                ">
                <table style="
                    border-collapse:separate;
                    border-spacing:5px;
                    margin:auto;
                ">
                """

                for r in range(1, layout.rows + 1):

                    html += "<tr>"

                    for c in range(1, layout.columns + 1):

                        seat = grid.get((r, c))

                        if seat is None:

                            bg = "#E2E8F0"
                            border = "#94A3B8"
                            color = "#475569"
                            label = "?"

                        elif seat.is_available:

                            bg = "#DCFCE7"
                            border = "#16A36A"
                            color = "#166534"
                            label = seat.seat_code

                        else:

                            bg = "#FEE2E2"
                            border = "#DC4545"
                            color = "#991B1B"
                            label = "X"

                        html += (
                            "<td style='"
                            f"background:{bg};"
                            f"border:1px solid {border};"
                            f"color:{color};"
                            "width:65px;"
                            "height:42px;"
                            "text-align:center;"
                            "border-radius:7px;"
                            "font-size:11px;"
                            "font-weight:600;"
                            "padding:4px;"
                            "'>"
                            f"{label}"
                            "</td>"
                        )

                    html += "</tr>"

                html += "</table></div>"

                st.markdown(
                    html,
                    unsafe_allow_html=True,
                )

                st.write("")

                legend1, legend2, legend3 = st.columns(3)

                with legend1:

                    st.success("Available")

                with legend2:

                    st.error("Unavailable")

                with legend3:

                    st.info("Missing seat")

                # ----------------------------------
                # ADJACENCY PREVIEW
                # ----------------------------------

                with st.expander(
                    "View Seat Adjacency Information"
                ):

                    adj = build_adjacency_list(
                        layout,
                        mode="horizontal_vertical",
                    )

                    examples = []

                    for seat in layout.seats[:8]:

                        if seat.is_available:

                            neighbors = adj.get(
                                seat.seat_id,
                                [],
                            )

                            neighbor_codes = [
                                ns.seat_code
                                for ns in layout.seats
                                if ns.seat_id in neighbors
                            ]

                            examples.append(
                                {
                                    "Seat": seat.seat_code,
                                    "Adjacent Seats": (
                                        ", ".join(neighbor_codes)
                                        or "None"
                                    ),
                                }
                            )

                    if examples:

                        st.dataframe(
                            pd.DataFrame(examples),
                            use_container_width=True,
                            hide_index=True,
                        )

                    else:

                        st.info(
                            "No available seat adjacency information."
                        )


# ==================================================
# TAB 4: EDIT SEAT AVAILABILITY
# ==================================================

with tab_edit:

    st.subheader("Seat Availability Management")

    st.caption(
        "Select a classroom and mark individual seats "
        "as available or unavailable."
    )

    with get_db_session() as db:

        summaries = get_layout_summary(db)

    if not summaries:

        st.info(
            "No classrooms are available for editing. "
            "Create a classroom layout first."
        )

    else:

        room_options = {
            f"{s['room_id']} - {s['room_name']}": s["classroom_id"]
            for s in summaries
        }

        selected_label = st.selectbox(
            "Select Classroom to Edit",
            list(room_options.keys()),
            key="edit_select",
        )

        if selected_label:

            cid = room_options[selected_label]

            with get_db_session() as db:

                layout = get_classroom_layout(db, cid)

            if layout:

                st.divider()

                st.markdown("### Classroom Summary")

                summary1, summary2, summary3 = st.columns(3)

                with summary1:

                    st.metric(
                        "Total Seats",
                        layout.total_seats,
                    )

                with summary2:

                    st.metric(
                        "Available Seats",
                        layout.usable_seats,
                    )

                with summary3:

                    st.metric(
                        "Unavailable Seats",
                        layout.total_seats - layout.usable_seats,
                    )

                st.divider()

                st.markdown("### Seat Records")

                seat_data = [
                    {
                        "Seat ID": seat.seat_id,
                        "Seat Code": seat.seat_code,
                        "Row": seat.row,
                        "Column": seat.col,
                        "Available": seat.is_available,
                        "Confirmed": seat.is_confirmed,
                    }
                    for seat in layout.seats
                ]

                st.dataframe(
                    pd.DataFrame(seat_data),
                    use_container_width=True,
                    hide_index=True,
                )

                st.divider()

                st.markdown("### Update Seat Status")

                seat_codes = [
                    seat.seat_code
                    for seat in layout.seats
                ]

                if not seat_codes:

                    st.warning(
                        "This classroom does not contain any seats."
                    )

                else:

                    with st.container(border=True):

                        col1, col2 = st.columns(2)

                        with col1:

                            chosen_code = st.selectbox(
                                "Select Seat",
                                seat_codes,
                            )

                        with col2:

                            new_status = st.selectbox(
                                "New Availability Status",
                                ["Available", "Unavailable"],
                            )

                        reason = st.text_input(
                            "Reason (if unavailable)",
                            placeholder="Example: Broken desk / Reserved",
                        )

                        if st.button(
                            "Update Seat Status",
                            type="primary",
                            use_container_width=True,
                        ):

                            seat = next(
                                seat
                                for seat in layout.seats
                                if seat.seat_code == chosen_code
                            )

                            with get_db_session() as db:

                                success, msg = set_seat_availability(
                                    db,
                                    seat_id=seat.seat_id,
                                    is_available=(
                                        new_status == "Available"
                                    ),
                                    reason=(
                                        reason
                                        if new_status == "Unavailable"
                                        else None
                                    ),
                                )

                            if success:

                                st.success(msg)
                                st.rerun()

                            else:

                                st.error(msg)

                st.divider()

                st.markdown("### Confirm Classroom Layout")

                st.warning(
                    "Confirm the layout only after reviewing "
                    "the classroom and its seat availability."
                )

                if st.button(
                    "Confirm Entire Layout",
                    type="primary",
                    use_container_width=True,
                ):

                    with get_db_session() as db:

                        success, msg = confirm_layout(db, cid)

                    if success:

                        st.success(msg)

                    else:

                        st.error(msg)


# ==================================================
# FOOTER
# ==================================================

st.divider()

st.caption(
    "EXAMFLOW | Classroom Layout Management | "
    "Manual Layout & Computer Vision"
)
