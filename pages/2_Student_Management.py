
"""
EXAMFLOW - Student, Classroom & Supervisor Management
Manage examination resources through CSV and Excel imports.
"""

import importlib
import streamlit as st
import pandas as pd

import ui.theme
importlib.reload(ui.theme)
from ui.theme import apply_theme
from database.connection import init_db, get_db_session
from database import repository as repo

from services.import_service import (
    read_uploaded_file,
    import_students,
    import_classrooms,
    import_supervisors,
)

from services.validation_service import (
    validate_students,
    validate_classrooms,
    validate_supervisors,
)

from config import TEMPLATES_DIR


# --------------------------------------------------
# SHARED THEME AND INITIALIZATION
# --------------------------------------------------

apply_theme()
init_db()


# --------------------------------------------------
# PAGE HEADER
# --------------------------------------------------

st.title("Student & Data Management")

st.markdown(
    "Manage students, classrooms, and examination supervisors "
    "from one centralized workspace."
)

st.write("")

st.info(
    "Import your examination data using CSV or Excel files. "
    "Review the uploaded records before confirming an import."
)


# --------------------------------------------------
# MANAGEMENT TABS
# --------------------------------------------------

tab_students, tab_classrooms, tab_supervisors, tab_view = st.tabs(
    [
        "👨‍🎓 Students",
        "🏫 Classrooms",
        "👨‍🏫 Supervisors",
        "📊 View Current Data",
    ]
)


# ==================================================
# STUDENTS TAB
# ==================================================

with tab_students:

    st.subheader("Student Management")

    st.caption(
        "Import student records and validate them before "
        "adding them to the examination database."
    )

    with st.container(border=True):

        st.markdown("**Required CSV / Excel columns**")

        st.code(
            "student_id, roll_number, student_name, batch",
            language="text",
        )

        template_path = TEMPLATES_DIR / "students_template.csv"

        if template_path.exists():

            with open(template_path, "rb") as f:

                st.download_button(
                    "Download Students Template",
                    f,
                    file_name="students_template.csv",
                    mime="text/csv",
                    use_container_width=False,
                )

    st.write("")

    uploaded = st.file_uploader(
        "Upload Student File",
        type=["csv", "xlsx"],
        key="students_uploader",
        help="Upload a CSV or Excel file containing student records.",
    )

    if uploaded is not None:

        try:

            df = read_uploaded_file(uploaded)

            st.markdown("### Uploaded File Preview")

            st.caption("Showing the first 20 records.")

            st.dataframe(
                df.head(20),
                use_container_width=True,
                hide_index=True,
            )

            is_valid, errors, clean_df = validate_students(df)

            st.divider()

            if not is_valid:

                st.error("Student data validation failed.")

                for error in errors:
                    st.write(f"- {error}")

            else:

                st.success(
                    f"Validation successful! "
                    f"{len(clean_df)} student records are ready."
                )

                with st.expander("View Cleaned Student Data"):

                    st.dataframe(
                        clean_df.head(20),
                        use_container_width=True,
                        hide_index=True,
                    )

                replace = st.checkbox(
                    "Replace all existing students",
                    value=False,
                    key="replace_students",
                    help="This replaces previously imported student records.",
                )

                if st.button(
                    "Confirm & Import Students",
                    type="primary",
                    key="btn_import_students",
                    use_container_width=True,
                ):

                    with get_db_session() as db:

                        success, message, count = import_students(
                            db,
                            df,
                            replace_existing=replace,
                        )

                    if success:

                        st.success(message)
                        st.balloons()

                    else:

                        st.error(message)

        except Exception as e:

            st.error(f"Error reading student file: {e}")


# ==================================================
# CLASSROOMS TAB
# ==================================================

with tab_classrooms:

    st.subheader("Classroom Management")

    st.caption(
        "Register examination rooms and their seating capacity."
    )

    with st.container(border=True):

        st.markdown("**Required CSV / Excel columns**")

        st.code(
            "room_id, room_name, rows, columns",
            language="text",
        )

        st.caption(
            "Optional column: is_available (true / false)"
        )

        template_path = TEMPLATES_DIR / "classrooms_template.csv"

        if template_path.exists():

            with open(template_path, "rb") as f:

                st.download_button(
                    "Download Classrooms Template",
                    f,
                    file_name="classrooms_template.csv",
                    mime="text/csv",
                )

    st.write("")

    uploaded = st.file_uploader(
        "Upload Classroom File",
        type=["csv", "xlsx"],
        key="classrooms_uploader",
        help="Upload a CSV or Excel file containing classroom details.",
    )

    if uploaded is not None:

        try:

            df = read_uploaded_file(uploaded)

            st.markdown("### Uploaded File Preview")

            st.dataframe(
                df.head(20),
                use_container_width=True,
                hide_index=True,
            )

            is_valid, errors, clean_df = validate_classrooms(df)

            st.divider()

            if not is_valid:

                st.error("Classroom data validation failed.")

                for error in errors:
                    st.write(f"- {error}")

            else:

                st.success(
                    f"Validation successful! "
                    f"{len(clean_df)} classroom records are ready."
                )

                st.info(
                    "Seats will be automatically generated "
                    "when classrooms are imported."
                )

                with st.expander("View Cleaned Classroom Data"):

                    st.dataframe(
                        clean_df,
                        use_container_width=True,
                        hide_index=True,
                    )

                replace = st.checkbox(
                    "Replace all existing classrooms and their seats",
                    value=False,
                    key="replace_classrooms",
                )

                if st.button(
                    "Confirm & Import Classrooms",
                    type="primary",
                    key="btn_import_classrooms",
                    use_container_width=True,
                ):

                    with get_db_session() as db:

                        success, message, count = import_classrooms(
                            db,
                            df,
                            replace_existing=replace,
                        )

                    if success:

                        st.success(message)
                        st.balloons()

                    else:

                        st.error(message)

        except Exception as e:

            st.error(f"Error reading classroom file: {e}")


# ==================================================
# SUPERVISORS TAB
# ==================================================

with tab_supervisors:

    st.subheader("Supervisor Management")

    st.caption(
        "Register examination supervisors and manage their availability."
    )

    with st.container(border=True):

        st.markdown("**Required CSV / Excel columns**")

        st.code(
            "supervisor_id, supervisor_name",
            language="text",
        )

        st.caption(
            "Optional column: is_available (true / false)"
        )

        template_path = TEMPLATES_DIR / "supervisors_template.csv"

        if template_path.exists():

            with open(template_path, "rb") as f:

                st.download_button(
                    "Download Supervisors Template",
                    f,
                    file_name="supervisors_template.csv",
                    mime="text/csv",
                )

    st.write("")

    uploaded = st.file_uploader(
        "Upload Supervisor File",
        type=["csv", "xlsx"],
        key="supervisors_uploader",
        help="Upload a CSV or Excel file containing supervisor details.",
    )

    if uploaded is not None:

        try:

            df = read_uploaded_file(uploaded)

            st.markdown("### Uploaded File Preview")

            st.dataframe(
                df.head(20),
                use_container_width=True,
                hide_index=True,
            )

            is_valid, errors, clean_df = validate_supervisors(df)

            st.divider()

            if not is_valid:

                st.error("Supervisor data validation failed.")

                for error in errors:
                    st.write(f"- {error}")

            else:

                st.success(
                    f"Validation successful! "
                    f"{len(clean_df)} supervisors are ready."
                )

                with st.expander("View Cleaned Supervisor Data"):

                    st.dataframe(
                        clean_df,
                        use_container_width=True,
                        hide_index=True,
                    )

                replace = st.checkbox(
                    "Replace all existing supervisors",
                    value=False,
                    key="replace_supervisors",
                )

                if st.button(
                    "Confirm & Import Supervisors",
                    type="primary",
                    key="btn_import_supervisors",
                    use_container_width=True,
                ):

                    with get_db_session() as db:

                        success, message, count = import_supervisors(
                            db,
                            df,
                            replace_existing=replace,
                        )

                    if success:

                        st.success(message)
                        st.balloons()

                    else:

                        st.error(message)

        except Exception as e:

            st.error(f"Error reading supervisor file: {e}")


# ==================================================
# VIEW CURRENT DATA TAB
# ==================================================

with tab_view:

    st.subheader("Current Database Records")

    st.caption(
        "View all currently registered students, classrooms, "
        "supervisors, and available seats."
    )

    # Retrieve plain dictionaries while the session is open.
    with get_db_session() as db:

        students_data = [
            {
                "student_id": s.student_id,
                "roll_number": s.roll_number,
                "student_name": s.student_name,
                "batch": s.batch,
            }
            for s in repo.get_all_students(db)
        ]

        classrooms_data = [
            {
                "room_id": c.room_id,
                "room_name": c.room_name,
                "rows": c.rows,
                "columns": c.columns,
                "is_available": c.is_available,
                "layout_source": c.layout_source,
            }
            for c in repo.get_all_classrooms(db)
        ]

        supervisors_data = [
            {
                "supervisor_id": s.supervisor_id,
                "supervisor_name": s.supervisor_name,
                "is_available": s.is_available,
            }
            for s in repo.get_all_supervisors(db)
        ]

        n_seats = repo.count_available_seats(db)

    # ----------------------------------------------
    # DATABASE SUMMARY
    # ----------------------------------------------

    st.markdown("### Resource Summary")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Students",
        len(students_data),
    )

    col2.metric(
        "Classrooms",
        len(classrooms_data),
    )

    col3.metric(
        "Usable Seats",
        n_seats,
    )

    col4.metric(
        "Supervisors",
        len(supervisors_data),
    )

    st.divider()

    # ----------------------------------------------
    # STUDENT RECORDS
    # ----------------------------------------------

    st.markdown("### Student Records")

    if students_data:

        st.dataframe(
            pd.DataFrame(students_data),
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info("No students have been imported yet.")

    st.divider()

    # ----------------------------------------------
    # CLASSROOM RECORDS
    # ----------------------------------------------

    st.markdown("### Classroom Records")

    if classrooms_data:

        st.dataframe(
            pd.DataFrame(classrooms_data),
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info("No classrooms have been imported yet.")

    st.divider()

    # ----------------------------------------------
    # SUPERVISOR RECORDS
    # ----------------------------------------------

    st.markdown("### Supervisor Records")

    if supervisors_data:

        st.dataframe(
            pd.DataFrame(supervisors_data),
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info("No supervisors have been imported yet.")


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "EXAMFLOW | Student, Classroom & Supervisor Management"
)
