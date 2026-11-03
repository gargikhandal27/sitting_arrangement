"""
Student, Classroom & Supervisor Management – Phase 4+
"""
import streamlit as st
import pandas as pd

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

st.title("👨‍🎓 Data Management")
st.markdown("Import and manage **Students**, **Classrooms**, and **Supervisors**.")

init_db()

tab_students, tab_classrooms, tab_supervisors, tab_view = st.tabs(
    ["Import Students", "Import Classrooms", "Import Supervisors", "View Current Data"]
)

# -------------------------------------------------
# STUDENTS TAB
# -------------------------------------------------
with tab_students:
    st.subheader("Import Students (CSV / Excel)")
    st.markdown("**Required columns:** `student_id`, `roll_number`, `student_name`, `batch`")

    template_path = TEMPLATES_DIR / "students_template.csv"
    if template_path.exists():
        with open(template_path, "rb") as f:
            st.download_button(
                "Download Students Template (CSV)",
                f,
                file_name="students_template.csv",
                mime="text/csv",
            )

    uploaded = st.file_uploader("Upload student file", type=["csv", "xlsx"], key="students_uploader")

    if uploaded is not None:
        try:
            df = read_uploaded_file(uploaded)
            st.write("### Preview (first 20 rows)")
            st.dataframe(df.head(20), use_container_width=True)

            is_valid, errors, clean_df = validate_students(df)

            if not is_valid:
                st.error("Validation failed:")
                for e in errors:
                    st.write(f"- {e}")
            else:
                st.success(f"Validation passed. {len(clean_df)} valid student records ready.")
                st.write("### Cleaned data preview")
                st.dataframe(clean_df.head(20), use_container_width=True)

                replace = st.checkbox("Replace all existing students", value=False, key="replace_students")
                if st.button("Confirm & Import Students", type="primary", key="btn_import_students"):
                    with get_db_session() as db:
                        success, message, count = import_students(db, df, replace_existing=replace)
                    if success:
                        st.success(message)
                        st.balloons()
                    else:
                        st.error(message)
        except Exception as e:
            st.error(f"Error reading file: {e}")

# -------------------------------------------------
# CLASSROOMS TAB
# -------------------------------------------------
with tab_classrooms:
    st.subheader("Import Classrooms (CSV / Excel)")
    st.markdown("**Required columns:** `room_id`, `room_name`, `rows`, `columns`  \nOptional: `is_available` (true/false)")

    template_path = TEMPLATES_DIR / "classrooms_template.csv"
    if template_path.exists():
        with open(template_path, "rb") as f:
            st.download_button(
                "Download Classrooms Template (CSV)",
                f,
                file_name="classrooms_template.csv",
                mime="text/csv",
            )

    uploaded = st.file_uploader("Upload classroom file", type=["csv", "xlsx"], key="classrooms_uploader")

    if uploaded is not None:
        try:
            df = read_uploaded_file(uploaded)
            st.write("### Preview")
            st.dataframe(df.head(20), use_container_width=True)

            is_valid, errors, clean_df = validate_classrooms(df)

            if not is_valid:
                st.error("Validation failed:")
                for e in errors:
                    st.write(f"- {e}")
            else:
                st.success(f"Validation passed. {len(clean_df)} classroom(s) ready. Seats will be auto-generated.")
                st.dataframe(clean_df, use_container_width=True)

                replace = st.checkbox("Replace all existing classrooms (and their seats)", value=False, key="replace_classrooms")
                if st.button("Confirm & Import Classrooms", type="primary", key="btn_import_classrooms"):
                    with get_db_session() as db:
                        success, message, count = import_classrooms(db, df, replace_existing=replace)
                    if success:
                        st.success(message)
                        st.balloons()
                    else:
                        st.error(message)
        except Exception as e:
            st.error(f"Error reading file: {e}")

# -------------------------------------------------
# SUPERVISORS TAB
# -------------------------------------------------
with tab_supervisors:
    st.subheader("Import Supervisors (CSV / Excel)")
    st.markdown("**Required columns:** `supervisor_id`, `supervisor_name`  \nOptional: `is_available` (true/false)")

    template_path = TEMPLATES_DIR / "supervisors_template.csv"
    if template_path.exists():
        with open(template_path, "rb") as f:
            st.download_button(
                "Download Supervisors Template (CSV)",
                f,
                file_name="supervisors_template.csv",
                mime="text/csv",
            )

    uploaded = st.file_uploader("Upload supervisor file", type=["csv", "xlsx"], key="supervisors_uploader")

    if uploaded is not None:
        try:
            df = read_uploaded_file(uploaded)
            st.write("### Preview")
            st.dataframe(df.head(20), use_container_width=True)

            is_valid, errors, clean_df = validate_supervisors(df)

            if not is_valid:
                st.error("Validation failed:")
                for e in errors:
                    st.write(f"- {e}")
            else:
                st.success(f"Validation passed. {len(clean_df)} supervisor(s) ready.")
                st.dataframe(clean_df, use_container_width=True)

                replace = st.checkbox("Replace all existing supervisors", value=False, key="replace_supervisors")
                if st.button("Confirm & Import Supervisors", type="primary", key="btn_import_supervisors"):
                    with get_db_session() as db:
                        success, message, count = import_supervisors(db, df, replace_existing=replace)
                    if success:
                        st.success(message)
                        st.balloons()
                    else:
                        st.error(message)
        except Exception as e:
            st.error(f"Error reading file: {e}")

# -------------------------------------------------
# VIEW DATA TAB  (FIXED – convert to dicts inside the session)
# -------------------------------------------------
with tab_view:
    st.subheader("Currently Stored Data")

    # Convert ORM objects to plain dicts WHILE the session is still open
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

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Students", len(students_data))
    col2.metric("Classrooms", len(classrooms_data))
    col3.metric("Usable Seats", n_seats)
    col4.metric("Supervisors", len(supervisors_data))

    st.markdown("### Students")
    if students_data:
        st.dataframe(pd.DataFrame(students_data), use_container_width=True)
    else:
        st.info("No students imported yet.")

    st.markdown("### Classrooms")
    if classrooms_data:
        st.dataframe(pd.DataFrame(classrooms_data), use_container_width=True)
    else:
        st.info("No classrooms imported yet.")

    st.markdown("### Supervisors")
    if supervisors_data:
        st.dataframe(pd.DataFrame(supervisors_data), use_container_width=True)
    else:
        st.info("No supervisors imported yet.")
