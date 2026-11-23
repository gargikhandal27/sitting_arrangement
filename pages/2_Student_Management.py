
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

import services.validation_service
import services.import_service
importlib.reload(services.validation_service)
importlib.reload(services.import_service)

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
    repair_and_clean_students,
    repair_and_clean_classrooms,
    repair_and_clean_supervisors,
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

            file_cache_key = f"cache_parsed_stu_{uploaded.name}_{uploaded.size}"
            if file_cache_key not in st.session_state:
                parsed_df = read_uploaded_file(uploaded)
                is_val, errs, cln_df = validate_students(parsed_df)
                st.session_state[file_cache_key] = (parsed_df, is_val, errs, cln_df)

            df, is_valid, errors, clean_df = st.session_state[file_cache_key]

            st.markdown("### Uploaded File Preview")

            st.caption("Showing the first 20 records.")

            st.dataframe(
                df.head(20),
                use_container_width=True,
                hide_index=True,
            )

            st.divider()

            if not is_valid:

                st.error("Student data validation failed.")

                for error in errors:
                    st.write(f"- {error}")

                st.write("")
                with st.container(border=True):
                    st.markdown("### 🛠️ 1-Click Smart Auto-Clean & Repair")
                    st.markdown(
                        "ExamFlow can automatically resolve common student data issues: "
                        "fill in missing student names (e.g. 'Student <roll_number>'), resolve batches, "
                        "remove duplicate IDs/roll numbers, and trim blank rows."
                    )

                    if st.session_state.get("students_last_file") != uploaded.name:
                        st.session_state["students_last_file"] = uploaded.name
                        st.session_state["students_repaired_data"] = None

                    if st.button(
                        "✨ Auto-Clean & Repair Students Now",
                        type="primary",
                        key="btn_repair_students",
                        use_container_width=True,
                    ):
                        repaired_df, actions = repair_and_clean_students(df)
                        st.session_state["students_repaired_data"] = {
                            "df": repaired_df,
                            "actions": actions,
                            "initial_count": len(df),
                            "cleaned_count": len(repaired_df),
                        }
                        st.rerun()

                    repaired_info = st.session_state.get("students_repaired_data")
                    if repaired_info is not None:
                        repaired_df = repaired_info["df"]
                        actions = repaired_info["actions"]
                        initial_count = repaired_info["initial_count"]
                        cleaned_count = repaired_info["cleaned_count"]

                        st.success(
                            f"Student dataset repaired successfully! "
                            f"{cleaned_count} clean records are ready for import."
                        )

                        m1, m2, m3 = st.columns(3)
                        m1.metric("Original Rows", initial_count)
                        m2.metric("Clean Records", cleaned_count)
                        m3.metric("Status", "100% Ready")

                        with st.expander("🔍 See Auto-Repair Details (Actions Taken)", expanded=True):
                            for action in actions:
                                st.write(f"• {action}")

                        st.markdown("**Cleaned Student Data Preview**")
                        st.dataframe(
                            repaired_df.head(20),
                            use_container_width=True,
                            hide_index=True,
                        )

                        csv_data = repaired_df.to_csv(index=False).encode("utf-8")
                        st.download_button(
                            label="⬇️ Download Cleaned Students CSV",
                            data=csv_data,
                            file_name=f"cleaned_{uploaded.name.rsplit('.', 1)[0]}.csv",
                            mime="text/csv",
                            use_container_width=True,
                        )

                        st.divider()

                        replace_repaired = st.checkbox(
                            "Replace all existing students",
                            value=False,
                            key="replace_repaired_students",
                            help="This replaces previously imported student records.",
                        )

                        if st.button(
                            "Confirm & Import Cleaned Students",
                            type="primary",
                            key="btn_import_repaired_students",
                            use_container_width=True,
                        ):
                            with get_db_session() as db:
                                success, message, count = import_students(
                                    db,
                                    repaired_df,
                                    replace_existing=replace_repaired,
                                )

                            if success:
                                st.success(message)
                                st.balloons()
                            else:
                                st.error(message)

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

                csv_data = clean_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="⬇️ Download Cleaned Students CSV",
                    data=csv_data,
                    file_name=f"cleaned_{uploaded.name.rsplit('.', 1)[0]}.csv",
                    mime="text/csv",
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
                            clean_df,
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

            file_cache_key = f"cache_parsed_cls_{uploaded.name}_{uploaded.size}"
            if file_cache_key not in st.session_state:
                parsed_df = read_uploaded_file(uploaded)
                is_val, errs, cln_df = validate_classrooms(parsed_df)
                st.session_state[file_cache_key] = (parsed_df, is_val, errs, cln_df)

            df, is_valid, errors, clean_df = st.session_state[file_cache_key]

            st.markdown("### Uploaded File Preview")

            st.dataframe(
                df.head(20),
                use_container_width=True,
                hide_index=True,
            )

            st.divider()

            if not is_valid:

                st.error("Classroom data validation failed.")

                for error in errors:
                    st.write(f"- {error}")

                st.write("")
                with st.container(border=True):
                    st.markdown("### 🛠️ 1-Click Smart Auto-Clean & Repair")
                    st.markdown(
                        "ExamFlow can automatically resolve common classroom errors: "
                        "fill in missing room names, fix invalid grid dimensions (defaults to 5 rows x 6 columns), "
                        "remove duplicate room IDs, and prune blank rows."
                    )

                    if st.session_state.get("classrooms_last_file") != uploaded.name:
                        st.session_state["classrooms_last_file"] = uploaded.name
                        st.session_state["classrooms_repaired_data"] = None

                    if st.button(
                        "✨ Auto-Clean & Repair Classrooms Now",
                        type="primary",
                        key="btn_repair_classrooms",
                        use_container_width=True,
                    ):
                        repaired_df, actions = repair_and_clean_classrooms(df)
                        st.session_state["classrooms_repaired_data"] = {
                            "df": repaired_df,
                            "actions": actions,
                            "initial_count": len(df),
                            "cleaned_count": len(repaired_df),
                        }
                        st.rerun()

                    repaired_info = st.session_state.get("classrooms_repaired_data")
                    if repaired_info is not None:
                        repaired_df = repaired_info["df"]
                        actions = repaired_info["actions"]
                        initial_count = repaired_info["initial_count"]
                        cleaned_count = repaired_info["cleaned_count"]

                        st.success(
                            f"Classroom dataset repaired successfully! "
                            f"{cleaned_count} clean records are ready for import."
                        )

                        m1, m2, m3 = st.columns(3)
                        m1.metric("Original Rows", initial_count)
                        m2.metric("Clean Rooms", cleaned_count)
                        m3.metric("Status", "100% Ready")

                        with st.expander("🔍 See Auto-Repair Details (Actions Taken)", expanded=True):
                            for action in actions:
                                st.write(f"• {action}")

                        st.markdown("**Cleaned Classroom Data Preview**")
                        st.dataframe(repaired_df, use_container_width=True, hide_index=True)

                        csv_data = repaired_df.to_csv(index=False).encode("utf-8")
                        st.download_button(
                            label="⬇️ Download Cleaned Classrooms CSV",
                            data=csv_data,
                            file_name=f"cleaned_{uploaded.name.rsplit('.', 1)[0]}.csv",
                            mime="text/csv",
                            use_container_width=True,
                        )

                        st.divider()

                        replace_repaired = st.checkbox(
                            "Replace all existing classrooms and their seats",
                            value=False,
                            key="replace_repaired_classrooms",
                        )

                        if st.button(
                            "Confirm & Import Cleaned Classrooms",
                            type="primary",
                            key="btn_import_repaired_classrooms",
                            use_container_width=True,
                        ):
                            with get_db_session() as db:
                                success, message, count = import_classrooms(
                                    db,
                                    repaired_df,
                                    replace_existing=replace_repaired,
                                )

                            if success:
                                st.success(message)
                                st.balloons()
                            else:
                                st.error(message)

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

                csv_data = clean_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="⬇️ Download Cleaned Classrooms CSV",
                    data=csv_data,
                    file_name=f"cleaned_{uploaded.name.rsplit('.', 1)[0]}.csv",
                    mime="text/csv",
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
                            clean_df,
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

            file_cache_key = f"cache_parsed_sup_{uploaded.name}_{uploaded.size}"
            if file_cache_key not in st.session_state:
                parsed_df = read_uploaded_file(uploaded)
                is_val, errs, cln_df = validate_supervisors(parsed_df)
                st.session_state[file_cache_key] = (parsed_df, is_val, errs, cln_df)

            df, is_valid, errors, clean_df = st.session_state[file_cache_key]

            st.markdown("### Uploaded File Preview")

            st.dataframe(
                df.head(20),
                use_container_width=True,
                hide_index=True,
            )

            st.divider()

            if not is_valid:

                st.error("Supervisor data validation failed.")

                for error in errors:
                    st.write(f"- {error}")

                st.write("")
                with st.container(border=True):
                    st.markdown("### 🛠️ 1-Click Smart Auto-Clean & Repair")
                    st.markdown(
                        "ExamFlow can automatically resolve common supervisor errors: "
                        "generate missing supervisor IDs, fill default names, "
                        "remove duplicate IDs, and prune blank rows."
                    )

                    if st.session_state.get("supervisors_last_file") != uploaded.name:
                        st.session_state["supervisors_last_file"] = uploaded.name
                        st.session_state["supervisors_repaired_data"] = None

                    if st.button(
                        "✨ Auto-Clean & Repair Supervisors Now",
                        type="primary",
                        key="btn_repair_supervisors",
                        use_container_width=True,
                    ):
                        repaired_df, actions = repair_and_clean_supervisors(df)
                        st.session_state["supervisors_repaired_data"] = {
                            "df": repaired_df,
                            "actions": actions,
                            "initial_count": len(df),
                            "cleaned_count": len(repaired_df),
                        }
                        st.rerun()

                    repaired_info = st.session_state.get("supervisors_repaired_data")
                    if repaired_info is not None:
                        repaired_df = repaired_info["df"]
                        actions = repaired_info["actions"]
                        initial_count = repaired_info["initial_count"]
                        cleaned_count = repaired_info["cleaned_count"]

                        st.success(
                            f"Supervisor dataset repaired successfully! "
                            f"{cleaned_count} clean records are ready for import."
                        )

                        m1, m2, m3 = st.columns(3)
                        m1.metric("Original Rows", initial_count)
                        m2.metric("Clean Supervisors", cleaned_count)
                        m3.metric("Status", "100% Ready")

                        with st.expander("🔍 See Auto-Repair Details (Actions Taken)", expanded=True):
                            for action in actions:
                                st.write(f"• {action}")

                        st.markdown("**Cleaned Supervisor Data Preview**")
                        st.dataframe(repaired_df, use_container_width=True, hide_index=True)

                        csv_data = repaired_df.to_csv(index=False).encode("utf-8")
                        st.download_button(
                            label="⬇️ Download Cleaned Supervisors CSV",
                            data=csv_data,
                            file_name=f"cleaned_{uploaded.name.rsplit('.', 1)[0]}.csv",
                            mime="text/csv",
                            use_container_width=True,
                        )

                        st.divider()

                        replace_repaired = st.checkbox(
                            "Replace all existing supervisors",
                            value=False,
                            key="replace_repaired_supervisors",
                        )

                        if st.button(
                            "Confirm & Import Cleaned Supervisors",
                            type="primary",
                            key="btn_import_repaired_supervisors",
                            use_container_width=True,
                        ):
                            with get_db_session() as db:
                                success, message, count = import_supervisors(
                                    db,
                                    repaired_df,
                                    replace_existing=replace_repaired,
                                )

                            if success:
                                st.success(message)
                                st.balloons()
                            else:
                                st.error(message)

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

                csv_data = clean_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="⬇️ Download Cleaned Supervisors CSV",
                    data=csv_data,
                    file_name=f"cleaned_{uploaded.name.rsplit('.', 1)[0]}.csv",
                    mime="text/csv",
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
                            clean_df,
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

    # Retrieve database records efficiently
    with get_db_session() as db:

        total_students_count = repo.count_students(db)
        students_preview = repo.get_students_records_fast(db, limit=100)

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
        total_students_count,
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

    if total_students_count > 0:

        if total_students_count > 100:
            st.caption(f"Showing first 100 of {total_students_count} students (fast view).")
            show_all = st.checkbox(f"Show all {total_students_count} students", key="chk_show_all_students")
            if show_all:
                with get_db_session() as db:
                    all_students_data = repo.get_students_records_fast(db)
                st.dataframe(
                    pd.DataFrame(all_students_data),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.dataframe(
                    pd.DataFrame(students_preview),
                    use_container_width=True,
                    hide_index=True,
                )
        else:
            st.dataframe(
                pd.DataFrame(students_preview),
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
