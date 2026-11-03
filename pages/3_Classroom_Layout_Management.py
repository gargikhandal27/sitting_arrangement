"""
Classroom Layout Management
- Manual layout creation & editing (Phase 5)
- Computer Vision image analysis (Phase 6)
"""
import streamlit as st
import pandas as pd
from pathlib import Path

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

st.title("🏫 Classroom Layout Management")
st.markdown("Create layouts manually or analyse classroom images (Computer Vision).")

init_db()

tab_manual, tab_vision, tab_view, tab_edit = st.tabs([
    "Create Manual Layout",
    "Image Analysis (CV)",
    "View Layouts",
    "Edit Seats / Mark Unavailable",
])

# -------------------------------------------------
# CREATE MANUAL LAYOUT
# -------------------------------------------------
with tab_manual:
    st.subheader("Create a New Classroom (Grid Layout)")
    st.info("Creates a regular rectangular grid of seats. You can later mark individual seats as unavailable.")

    with st.form("create_classroom_form"):
        col1, col2 = st.columns(2)
        with col1:
            room_id = st.text_input("Room ID *", placeholder="e.g. R101")
            room_name = st.text_input("Room Name *", placeholder="e.g. Main Hall A")
        with col2:
            rows = st.number_input("Number of Rows *", min_value=1, max_value=30, value=5)
            columns = st.number_input("Number of Columns *", min_value=1, max_value=30, value=6)
        is_available = st.checkbox("Classroom is available", value=True)

        submitted = st.form_submit_button("Create Classroom & Generate Seats", type="primary")

        if submitted:
            if not room_id.strip() or not room_name.strip():
                st.error("Room ID and Room Name are required.")
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

# -------------------------------------------------
# IMAGE ANALYSIS (COMPUTER VISION)
# -------------------------------------------------
with tab_vision:
    st.subheader("Classroom Image Analysis (Computer Vision)")
    st.markdown("""
    **How it works (Phase 6 prototype):**
    1. Upload a classroom photograph or floor-plan
    2. OpenCV detects rectangular regions that may be desks/seats
    3. You review the annotated image
    4. You decide the final rows × columns and create the layout manually (or adjust later)
    
    **Important:** Detections are only proposals. The administrator must always confirm the final layout.
    """)

    uploaded = st.file_uploader(
        "Upload classroom photo or floor-plan",
        type=["jpg", "jpeg", "png", "bmp", "webp"],
        key="cv_uploader",
    )

    if uploaded is not None:
        # Show original
        st.image(uploaded, caption="Uploaded image", use_container_width=True)

        if st.button("Run Image Analysis", type="primary"):
            with st.spinner("Analysing image with OpenCV..."):
                try:
                    img_path = save_uploaded_image(uploaded)
                    result = analyze_classroom_image(img_path)

                    if not result.success:
                        st.error(result.message)
                    else:
                        st.success(result.message)
                        st.session_state["cv_result"] = result

                        if result.annotated_path and Path(result.annotated_path).exists():
                            st.image(result.annotated_path, caption="Annotated detections (green/orange boxes)", use_container_width=True)

                        st.write(f"**Detections:** {len(result.detections)}")
                        st.write(f"**Image size:** {result.image_width} × {result.image_height}")
                        st.write(f"**Method:** `{result.method}`")

                        if result.detections:
                            proposal = detections_to_grid_proposal(
                                result.detections,
                                result.image_width,
                                result.image_height,
                            )
                            st.info(
                                f"Rough grid estimate → rows ≈ {proposal['estimated_rows']}, "
                                f"columns ≈ {proposal['estimated_columns']} "
                                f"(based on {proposal['num_detections']} detections)"
                            )
                            st.caption(proposal["note"])

                            # Show detection table
                            det_df = pd.DataFrame([{
                                "id": i + 1,
                                "center_x": d.center_x,
                                "center_y": d.center_y,
                                "width": d.width,
                                "height": d.height,
                                "confidence": d.confidence,
                            } for i, d in enumerate(result.detections)])
                            st.dataframe(det_df, use_container_width=True, hide_index=True)
                except Exception as e:
                    st.error(f"Analysis failed: {e}")

        # After analysis – help user create a layout from the proposal
        if "cv_result" in st.session_state and st.session_state["cv_result"].success:
            st.markdown("---")
            st.subheader("Create Layout from Analysis")
            st.write("Use the detection results as a guide, then create a clean grid layout:")

            with st.form("cv_create_form"):
                c1, c2 = st.columns(2)
                with c1:
                    cv_room_id = st.text_input("Room ID *", value="R_CV_01")
                    cv_room_name = st.text_input("Room Name *", value="Classroom from Image")
                with c2:
                    cv_rows = st.number_input("Rows to create", min_value=1, max_value=30, value=5)
                    cv_cols = st.number_input("Columns to create", min_value=1, max_value=30, value=6)

                create_btn = st.form_submit_button("Create Classroom Layout", type="primary")
                if create_btn:
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
                        st.success(message + " You can now edit individual seats in the Edit tab.")
                        st.balloons()
                    else:
                        st.error(message)

# -------------------------------------------------
# VIEW LAYOUTS
# -------------------------------------------------
with tab_view:
    st.subheader("All Classroom Layouts")

    with get_db_session() as db:
        summaries = get_layout_summary(db)

    if not summaries:
        st.info("No classrooms created yet. Use Manual Layout or Image Analysis tabs.")
    else:
        st.dataframe(pd.DataFrame(summaries), use_container_width=True)

        st.markdown("---")
        st.subheader("Seat Grid Preview")

        room_options = {f"{s['room_id']} – {s['room_name']}": s["classroom_id"] for s in summaries}
        selected_label = st.selectbox("Select classroom to preview", list(room_options.keys()), key="view_select")

        if selected_label:
            cid = room_options[selected_label]
            with get_db_session() as db:
                layout = get_classroom_layout(db, cid)

            if layout and layout.rows and layout.columns:
                st.write(f"**{layout.room_id}** | {layout.usable_seats} usable / {layout.total_seats} total | Source: `{layout.layout_source}`")

                grid = {(s.row, s.col): s for s in layout.seats if s.row and s.col}

                html = "<table style='border-collapse:collapse; margin-top:10px;'>"
                for r in range(1, layout.rows + 1):
                    html += "<tr>"
                    for c in range(1, layout.columns + 1):
                        seat = grid.get((r, c))
                        if seat is None:
                            cell = "<td style='border:1px solid #ccc; width:48px; height:36px; text-align:center; background:#eee;'>?</td>"
                        elif seat.is_available:
                            cell = f"<td style='border:1px solid #4caf50; width:48px; height:36px; text-align:center; background:#e8f5e9; font-size:11px;'>{seat.seat_code}</td>"
                        else:
                            cell = f"<td style='border:1px solid #f44336; width:48px; height:36px; text-align:center; background:#ffebee; font-size:11px; color:#c62828;'>X</td>"
                        html += cell
                    html += "</tr>"
                html += "</table>"
                st.markdown(html, unsafe_allow_html=True)
                st.caption("Green = available · Red X = unavailable")

                with st.expander("Adjacency preview (horizontal + vertical)"):
                    adj = build_adjacency_list(layout, mode="horizontal_vertical")
                    examples = []
                    for s in layout.seats[:8]:
                        if s.is_available:
                            neighbors = adj.get(s.seat_id, [])
                            neighbor_codes = [ns.seat_code for ns in layout.seats if ns.seat_id in neighbors]
                            examples.append({"seat": s.seat_code, "neighbors": ", ".join(neighbor_codes) or "—"})
                    if examples:
                        st.dataframe(pd.DataFrame(examples), use_container_width=True)

# -------------------------------------------------
# EDIT SEATS
# -------------------------------------------------
with tab_edit:
    st.subheader("Mark Seats Available / Unavailable")

    with get_db_session() as db:
        summaries = get_layout_summary(db)

    if not summaries:
        st.info("No classrooms available.")
    else:
        room_options = {f"{s['room_id']} – {s['room_name']}": s["classroom_id"] for s in summaries}
        selected_label = st.selectbox("Select classroom", list(room_options.keys()), key="edit_select")

        if selected_label:
            cid = room_options[selected_label]
            with get_db_session() as db:
                layout = get_classroom_layout(db, cid)

            if layout:
                st.write(f"Editing **{layout.room_id}** ({layout.usable_seats} usable seats)")

                seat_data = [{
                    "seat_id": s.seat_id,
                    "seat_code": s.seat_code,
                    "row": s.row,
                    "col": s.col,
                    "available": s.is_available,
                    "confirmed": s.is_confirmed,
                } for s in layout.seats]
                st.dataframe(pd.DataFrame(seat_data), use_container_width=True, hide_index=True)

                st.markdown("#### Change availability of a seat")
                c1, c2, c3 = st.columns(3)
                with c1:
                    seat_codes = [s.seat_code for s in layout.seats]
                    chosen_code = st.selectbox("Seat code", seat_codes)
                with c2:
                    new_status = st.selectbox("New status", ["Available", "Unavailable"])
                with c3:
                    reason = st.text_input("Reason (if unavailable)", placeholder="Broken / reserved")

                if st.button("Update Seat Status", type="primary"):
                    seat = next(s for s in layout.seats if s.seat_code == chosen_code)
                    with get_db_session() as db:
                        success, msg = set_seat_availability(
                            db, seat_id=seat.seat_id,
                            is_available=(new_status == "Available"),
                            reason=reason if new_status == "Unavailable" else None,
                        )
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

                st.markdown("---")
                if st.button("Confirm entire layout"):
                    with get_db_session() as db:
                        success, msg = confirm_layout(db, cid)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)
