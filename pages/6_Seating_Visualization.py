
"""
Seating Visualization page
Displays actual assignments on classroom grids.
"""

import html
import streamlit as st
import pandas as pd

from collections import defaultdict

from ui.theme import apply_theme
from database.connection import init_db, get_db_session
from database.models import Classroom
from sqlalchemy import select
from services.classroom_layout_service import (
    get_all_layouts,
    get_classroom_layout,
)


# --------------------------------------------------
# PAGE SETUP
# --------------------------------------------------

apply_theme()
init_db()

st.title("🗺️ Seating Visualization")

st.markdown(
    "View the generated examination seating plan classroom by classroom. "
    "Occupied, empty, and unavailable seats are displayed separately."
)

st.divider()


# --------------------------------------------------
# GET LATEST SEATING RESULT
# --------------------------------------------------

seating_result = st.session_state.get("last_seating_result")

if (
    seating_result is None
    or not getattr(seating_result, "assignments", None)
):
    st.warning(
        "No seating plan is available yet. "
        "Please generate a seating plan on the Seating Generation page first."
    )

    st.info(
        "Once a seating plan has been generated successfully, "
        "the classroom seating charts and student assignments will appear here."
    )

else:

    # --------------------------------------------------
    # PLAN OVERVIEW
    # --------------------------------------------------

    st.header("Generated Seating Plan")

    with st.container(border=True):

        status = seating_result.status

        status_icons = {
            "OPTIMAL": "🟢",
            "FEASIBLE": "🔵",
            "INFEASIBLE": "🔴",
            "UNKNOWN": "🟠",
            "MODEL_INVALID": "🔴",
        }

        st.markdown(
            f"**Solver Status:** "
            f"{status_icons.get(status, '⚪')} {status}"
        )

        metric1, metric2 = st.columns(2)

        with metric1:
            st.metric(
                "Students Assigned",
                seating_result.students_assigned,
            )

        with metric2:
            st.metric(
                "Classrooms Used",
                seating_result.rooms_used,
            )

    # --------------------------------------------------
    # GROUP ASSIGNMENTS BY ROOM
    # --------------------------------------------------

    by_room = defaultdict(list)

    for assignment in seating_result.assignments:
        by_room[assignment["room_id"]].append(assignment)

    room_ids = sorted(by_room.keys())

    st.divider()
    st.header("Classroom Seating Chart")

    selected_room = st.selectbox(
        "Select Classroom",
        options=room_ids,
        help="Choose a classroom to view its seating arrangement.",
    )

    if selected_room:

        room_assignments = by_room[selected_room]

        # Map row and column positions to student assignments.
        position_map = {}

        for assignment in room_assignments:
            row = assignment.get("row")
            column = assignment.get("column")

            if row is not None and column is not None:
                position_map[(row, column)] = assignment

        # --------------------------------------------------
        # LOAD CLASSROOM LAYOUT
        # --------------------------------------------------

        
        with get_db_session() as db:
            classroom = db.scalar(
                select(Classroom).where(
                    Classroom.room_id == selected_room
                )
            )

            layout = (
                get_classroom_layout(db, classroom.id)
                if classroom is not None
                else None
            )


        if layout and layout.rows and layout.columns:

            st.subheader(
                f"{layout.room_id} — {layout.room_name}"
            )

            # --------------------------------------------------
            # CLASSROOM METRICS
            # --------------------------------------------------

            occupied_count = len(room_assignments)
            usable_seats = layout.usable_seats

            empty_count = max(
                0,
                usable_seats - occupied_count,
            )

            metric1, metric2, metric3 = st.columns(3)

            with metric1:
                st.metric(
                    "Occupied Seats",
                    occupied_count,
                )

            with metric2:
                st.metric(
                    "Empty Available Seats",
                    empty_count,
                )

            with metric3:
                st.metric(
                    "Total Seats",
                    layout.total_seats,
                )

            st.divider()

            # --------------------------------------------------
            # SEAT LEGEND
            # --------------------------------------------------

            st.subheader("Seat Status Legend")

            legend1, legend2, legend3 = st.columns(3)

            with legend1:
                st.markdown(
                    '<div style="background:#DCEBFA; color:#142B4A; '
                    'padding:10px; border-radius:8px; text-align:center; '
                    'border:1px solid #2878C8;">'
                    '<b>Occupied</b></div>',
                    unsafe_allow_html=True,
                )

            with legend2:
                st.markdown(
                    '<div style="background:#DDF3E7; color:#145A32; '
                    'padding:10px; border-radius:8px; text-align:center; '
                    'border:1px solid #16A36A;">'
                    '<b>Available</b></div>',
                    unsafe_allow_html=True,
                )

            with legend3:
                st.markdown(
                    '<div style="background:#FCE3E3; color:#922B21; '
                    'padding:10px; border-radius:8px; text-align:center; '
                    'border:1px solid #DC4545;">'
                    '<b>Unavailable</b></div>',
                    unsafe_allow_html=True,
                )

            # --------------------------------------------------
            # BUILD SEATING GRID
            # --------------------------------------------------

            st.subheader("Visual Seating Layout")

            html_grid = """
            <div style="overflow-x:auto; padding:8px 0;">
            <table style="
                border-collapse:separate;
                border-spacing:5px;
                margin:auto;
                text-align:center;
            ">
            """

            for row in range(1, layout.rows + 1):

                html_grid += "<tr>"

                for column in range(1, layout.columns + 1):

                    seat = next(
                        (
                            seat
                            for seat in layout.seats
                            if seat.row == row
                            and seat.col == column
                        ),
                        None,
                    )

                    assignment = position_map.get(
                        (row, column)
                    )

                    if seat is None:

                        background = "#E5E7EB"
                        border = "#9CA3AF"
                        text_color = "#52657D"
                        content = "?"

                    elif not seat.is_available:

                        background = "#FCE3E3"
                        border = "#DC4545"
                        text_color = "#922B21"
                        content = "UNAVAILABLE"

                    elif assignment:

                        background = "#DCEBFA"
                        border = "#2878C8"
                        text_color = "#142B4A"

                        roll_number = html.escape(
                            str(assignment.get("roll_number", ""))
                        )

                        batch = html.escape(
                            str(assignment.get("batch", ""))
                        )

                        content = (
                            f"<b>{roll_number}</b>"
                            f"<br>"
                            f"<span style='font-size:10px;'>"
                            f"{batch}</span>"
                        )

                    else:

                        background = "#DDF3E7"
                        border = "#16A36A"
                        text_color = "#145A32"

                        content = html.escape(
                            str(seat.seat_code)
                        )

                    html_grid += (
                        "<td style='"
                        "min-width:78px;"
                        "height:55px;"
                        "padding:5px;"
                        "text-align:center;"
                        "vertical-align:middle;"
                        "border-radius:7px;"
                        "border:1px solid "
                        f"{border};"
                        f"background:{background};"
                        f"color:{text_color};"
                        "font-size:11px;"
                        "font-family:Arial,sans-serif;"
                        "'>"
                        f"{content}"
                        "</td>"
                    )

                html_grid += "</tr>"

            html_grid += """
            </table>
            </div>
            """

            st.markdown(
                html_grid,
                unsafe_allow_html=True,
            )

            st.caption(
                "Occupied seats display the student's roll number and batch. "
                "Available seats display their seat code. "
                "Unavailable seats are marked separately."
            )

            # --------------------------------------------------
            # STUDENT ASSIGNMENT TABLE
            # --------------------------------------------------

            st.divider()
            st.subheader("Student Assignments")

            display_columns = [
                "student_id",
                "roll_number",
                "student_name",
                "batch",
                "seat_code",
                "row",
                "column",
            ]

            df = pd.DataFrame(room_assignments)

            available_columns = [
                column
                for column in display_columns
                if column in df.columns
            ]

            df = df[available_columns]

            st.caption(
                f"{len(room_assignments)} student assignment records "
                f"for {selected_room}."
            )

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
            )

            # --------------------------------------------------
            # DOWNLOAD ROOM ASSIGNMENTS
            # --------------------------------------------------

            csv_data = df.to_csv(
                index=False
            ).encode("utf-8")

            st.download_button(
                "⬇️ Download This Classroom's Assignments",
                data=csv_data,
                file_name=f"{selected_room}_assignments.csv",
                mime="text/csv",
                use_container_width=True,
            )

        else:

            st.warning(
                "Could not load the classroom layout details "
                "for this room. Please check the classroom configuration."
            )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "EXAMFLOW · Seating Visualization"
)
