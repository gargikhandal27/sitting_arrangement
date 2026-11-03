"""
Seating Visualization page – shows actual assignments on classroom grids
"""
import streamlit as st
import pandas as pd
from collections import defaultdict

from database.connection import init_db, get_db_session
from services.classroom_layout_service import get_all_layouts, get_classroom_layout

st.title("🗺️ Seating Visualization")
st.markdown("Visual seating charts based on the latest generated plan.")

init_db()

seating_result = st.session_state.get("last_seating_result")

if seating_result is None or not getattr(seating_result, "assignments", None):
    st.warning("No seating plan found. Please run **Seating Generation** first.")
else:
    st.success(
        f"Showing plan: {seating_result.students_assigned} students in "
        f"{seating_result.rooms_used} room(s) | Status: {seating_result.status}"
    )

    # Group assignments by room
    by_room = defaultdict(list)
    for a in seating_result.assignments:
        by_room[a["room_id"]].append(a)

    room_ids = sorted(by_room.keys())
    selected_room = st.selectbox("Select classroom", room_ids)

    if selected_room:
        room_assignments = by_room[selected_room]
        # Map (row, col) -> assignment
        pos_map = {}
        for a in room_assignments:
            r, c = a.get("row"), a.get("column")
            if r is not None and c is not None:
                pos_map[(r, c)] = a

        with get_db_session() as db:
            layouts = get_all_layouts(db)
            layout = next((l for l in layouts if l.room_id == selected_room), None)

        if layout and layout.rows and layout.columns:
            st.write(
                f"**{layout.room_id} – {layout.room_name}** | "
                f"{len(room_assignments)} students seated | "
                f"{layout.usable_seats} usable seats"
            )

            # Build visual grid
            html = "<table style='border-collapse:collapse; margin-top:12px;'>"
            for r in range(1, layout.rows + 1):
                html += "<tr>"
                for c in range(1, layout.columns + 1):
                    seat = next((s for s in layout.seats if s.row == r and s.col == c), None)
                    assign = pos_map.get((r, c))

                    if seat is None:
                        style = "background:#eee; border:1px solid #ccc;"
                        content = "?"
                    elif not seat.is_available:
                        style = "background:#ffebee; border:1px solid #f44336; color:#c62828;"
                        content = "X"
                    elif assign:
                        style = "background:#e3f2fd; border:1px solid #1976d2; font-size:10px;"
                        content = f"{assign['roll_number']}<br/><span style='color:#555'>{assign['batch']}</span>"
                    else:
                        style = "background:#e8f5e9; border:1px solid #4caf50; font-size:11px;"
                        content = seat.seat_code

                    html += (
                        f"<td style='width:70px; height:48px; text-align:center; "
                        f"vertical-align:middle; {style}'>{content}</td>"
                    )
                html += "</tr>"
            html += "</table>"
            st.markdown(html, unsafe_allow_html=True)
            st.caption("Blue = occupied (shows roll & batch) · Green = empty · Red X = unavailable")

            # Table of assignments in this room
            st.subheader("Assignments in this room")
            df = pd.DataFrame(room_assignments)[
                ["student_id", "roll_number", "student_name", "batch", "seat_code", "row", "column"]
            ]
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("Could not load layout details for this room.")
