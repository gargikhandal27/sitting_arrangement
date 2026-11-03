"""
Dashboard page – Overview of system status
"""
import streamlit as st
from database.connection import init_db, get_db_session
from database import repository as repo

st.title("📊 Dashboard")
st.markdown("Overview of registered data and generated plans.")

try:
    init_db()
    db_status = "✅ Database connected & tables ready"
except Exception as e:
    db_status = f"❌ Database error: {e}"

st.caption(db_status)

try:
    with get_db_session() as db:
        n_students = repo.count_students(db)
        n_classrooms = repo.count_classrooms(db)
        n_seats = repo.count_available_seats(db)
        n_supervisors = repo.count_supervisors(db)
        n_plans = repo.count_plans(db)
except Exception as e:
    n_students = n_classrooms = n_seats = n_supervisors = n_plans = 0
    st.error(f"Could not read counts: {e}")

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Students", n_students)
col2.metric("Classrooms", n_classrooms)
col3.metric("Usable Seats", n_seats)
col4.metric("Supervisors", n_supervisors)
col5.metric("Seating Plans", n_plans)

st.divider()

st.subheader("Recent Examination Sessions")
st.write("No sessions yet. Sessions will appear here after data is imported and plans are generated.")

st.subheader("Quick Actions")
st.markdown("""
- Go to **Data Management** to import student / classroom / supervisor data  
- Go to **Classroom Layout Management** to create or analyse classroom layouts  
- Go to **Natural Language Requirements** to set constraints  
""")

st.success("Database is active. Import data from the Data Management page to see non-zero counts.")
