"""
Seating Generation Page
Create conflict-free seating plans, test scenarios, and view room capacity guides.
"""
from __future__ import annotations
import importlib
import pandas as pd
import streamlit as st

import ui.theme
importlib.reload(ui.theme)
from ui.theme import apply_theme
from database.connection import init_db, get_db_session
from services.allocation_service import (
    run_seating_generation,
    load_students_for_solver,
    load_supervisors_for_solver,
)
from services.classroom_layout_service import get_all_layouts
from services.infeasibility_agent import (
    diagnose_seating_feasibility,
    apply_negotiation_proposal,
    simulate_what_if_scenario,
    get_classroom_checkerboard_analysis,
)

# --------------------------------------------------
# PAGE SETUP
# --------------------------------------------------
apply_theme()
init_db()

st.title("🪑 Seating Plan Generator")
st.markdown(
    "Create an examination seating plan with automatic conflict-free spacing between students, "
    "test hypothetical scenarios, or check room capacity limits."
)

st.write("")

# --------------------------------------------------
# MAIN WORKSPACE TABS & DATA PREFETCH
# --------------------------------------------------
with get_db_session() as db:
    all_rooms_list = get_all_layouts(db)
    all_students_base = load_students_for_solver(db)

tab_plan, tab_what_if, tab_capacity = st.tabs([
    "🪑 Create Seating Plan",
    "🔮 Test Scenarios ('What-If')",
    "📐 Room Capacity Guide",
])

# ==================================================
# TAB 1: CREATE SEATING PLAN
# ==================================================
with tab_plan:
    # Load confirmed natural language settings
    nl_config = st.session_state.get("confirmed_nl_config", {})

    default_adj = nl_config.get("adjacency_mode", "horizontal_vertical")
    default_min = nl_config.get("minimize_classrooms", True)
    default_time = nl_config.get("solver_time_limit_seconds", 60) or 60
    default_time = max(5, min(300, int(default_time)))

    st.subheader("Solver Configuration")

    if nl_config:
        st.info(
            "Settings confirmed on the Natural Language Requirements "
            "page are being used as default values below. "
            "You can review or change them before generating."
        )

    # 1. Spacing Rule Selection
    mode_options = ["horizontal_vertical", "horizontal"]
    mode_labels = {
        "horizontal_vertical": "Strict Spacing (Skip next seat & row)",
        "horizontal": "Normal Spacing (Skip side-by-side seat only)",
    }

    current_mode_index = (
        mode_options.index(default_adj) if default_adj in mode_options else 0
    )

    adjacency_mode = st.selectbox(
        "Desk Spacing Rule",
        options=mode_options,
        index=current_mode_index,
        format_func=lambda x: mode_labels.get(x, x),
        help=(
            "Strict spacing keeps both side-by-side and front-to-back desks empty "
            "between students of the same class. Normal spacing keeps only side-by-side desks empty."
        ),
    )

    # 2. Classroom Filter Selection
    available_room_options = [lay.room_id for lay in all_rooms_list if lay.is_available and lay.usable_seats > 0]
    room_labels_map = {
        lay.room_id: f"{lay.room_name} ({lay.usable_seats} usable desks)"
        for lay in all_rooms_list
    }

    selected_room_ids = st.multiselect(
        "Active Classrooms to Use (Optional Filter)",
        options=available_room_options,
        default=available_room_options,
        format_func=lambda rid: room_labels_map.get(rid, rid),
        help="Select which classrooms to include in this exam seating plan.",
    )

    # Advanced Settings Expander
    with st.expander("⚙️ Advanced Solver Settings", expanded=False):
        time_limit = st.number_input(
            "Time Limit (seconds)",
            min_value=5,
            max_value=300,
            value=int(default_time),
            step=5,
            help="Maximum seconds the computer is allowed to search for an optimal solution.",
        )

        minimize_classrooms = st.checkbox(
            "Minimize the number of classrooms",
            value=bool(default_min),
            help="Ask the solver to use as few classrooms as possible while satisfying all rules.",
        )

    # Buttons: Quick Space Check & Create Seating Plan
    st.divider()
    st.subheader("Run Seating Generator")

    btn_col1, btn_col2 = st.columns([1, 1])

    with btn_col1:
        run_preflight = st.button(
            "🤖 Quick Check: Will Students Fit?",
            use_container_width=True,
            help="Quickly checks if classrooms have enough desks before planning.",
        )

    with btn_col2:
        run_solver = st.button(
            "🚀 Create Seating Plan",
            type="primary",
            use_container_width=True,
        )

    # Pre-flight check execution
    if run_preflight:
        with get_db_session() as db:
            students_list = load_students_for_solver(db)
            layouts_list = get_all_layouts(db)
            if selected_room_ids is not None:
                layouts_list = [lay for lay in layouts_list if lay.room_id in selected_room_ids]
            supervisors_list = load_supervisors_for_solver(db)

            diag_report = diagnose_seating_feasibility(
                students=students_list,
                layouts=layouts_list,
                adjacency_mode=adjacency_mode,
                time_limit_seconds=int(time_limit),
                supervisors=supervisors_list,
            )
            st.session_state["preflight_report"] = diag_report

    # Display Pre-flight Report if available
    if "preflight_report" in st.session_state:
        diag = st.session_state["preflight_report"]
        with st.container(border=True):
            st.subheader("🔍 Space Check Result")
            if diag.is_feasible:
                st.success(f"**All Good**: {diag.summary}")
            else:
                st.warning(f"**Attention Needed**: {diag.summary}")

            # Issues
            for issue in diag.issues:
                icon = "❌" if issue.severity == "error" else "⚠️"
                st.markdown(f"- **{icon} {issue.title}**: {issue.description}")

            # 1-Click Fixes
            if diag.remediations:
                st.markdown("##### 💡 Recommended Quick Fixes:")
                for idx, r in enumerate(diag.remediations):
                    with st.container(border=True):
                        p_col1, p_col2 = st.columns([3, 1])
                        with p_col1:
                            st.markdown(f"**{r.title}** · *{r.confidence_score}% Success Chance*")
                            st.write(r.description)
                            if r.trade_off:
                                st.caption(f"**What to keep in mind:** {r.trade_off}")
                            st.caption(f"**Benefit:** {r.impact}")
                        with p_col2:
                            if st.button("⚡ Apply Fix & Re-check", key=f"preflight_apply_{idx}", type="primary", use_container_width=True):
                                with get_db_session() as db:
                                    success, msg, ctx = apply_negotiation_proposal(r.id, db)
                                    if success:
                                        if "adjacency_mode" in ctx:
                                            st.session_state["confirmed_nl_config"] = st.session_state.get("confirmed_nl_config", {})
                                            st.session_state["confirmed_nl_config"]["adjacency_mode"] = ctx["adjacency_mode"]
                                        st.success(msg)
                                        st.session_state.pop("preflight_report", None)
                                        st.rerun()
                                    else:
                                        st.error(msg)

    # Seating solver execution
    if run_solver:
        try:
            with st.spinner("Creating exam seating plan. Please wait..."):
                with get_db_session() as db:
                    result, layouts = run_seating_generation(
                        db,
                        adjacency_mode=adjacency_mode,
                        minimize_classrooms=minimize_classrooms,
                        time_limit_seconds=int(time_limit),
                        selected_room_ids=selected_room_ids,
                    )

            st.session_state["last_seating_result"] = result
            st.session_state["last_seating_layouts"] = layouts
            st.session_state["seating_generation_completed"] = True

            # Run diagnosis if not optimal/feasible
            if result.status not in ("OPTIMAL", "FEASIBLE"):
                with get_db_session() as db:
                    students_list = load_students_for_solver(db)
                    supervisors_list = load_supervisors_for_solver(db)
                    diag = diagnose_seating_feasibility(
                        students=students_list,
                        layouts=layouts,
                        adjacency_mode=adjacency_mode,
                        time_limit_seconds=int(time_limit),
                        solver_result=result,
                        supervisors=supervisors_list,
                    )
                    st.session_state["infeasibility_diagnosis"] = diag

        except Exception as e:
            st.error(f"Seating generation failed: {e}")

    # Display results if a run has occurred
    if st.session_state.get("seating_generation_completed", False):
        result = st.session_state.get("last_seating_result")
        layouts = st.session_state.get("last_seating_layouts", [])

        st.divider()
        st.subheader("Seating Results")

        if result.status == "OPTIMAL":
            st.success(
                f"🎉 **Optimal seating plan generated!** All students seated "
                f"in {result.runtime_seconds:.2f} seconds."
            )
        elif result.status == "FEASIBLE":
            st.info(
                f"✅ **Valid seating plan generated!** All students seated "
                f"in {result.runtime_seconds:.2f} seconds."
            )
        else:
            st.error(
                f"⚠️ Could not generate a plan. Solver returned: **{result.status}**. "
                f"{result.message}"
            )

        # Result KPI Metrics
        assigned_students = getattr(result, "students_assigned", getattr(result, "total_students", len(getattr(result, "assignments", []))))
        used_rooms = getattr(result, "rooms_used", getattr(result, "classrooms_used", 0))
        runtime = getattr(result, "runtime_seconds", 0.0)

        r1, r2, r3, r4 = st.columns(4)
        with r1:
            st.metric("Total Students", assigned_students)
        with r2:
            st.metric("Students Seated", assigned_students)
        with r3:
            st.metric("Classrooms Used", used_rooms)
        with r4:
            st.metric("Calculation Time", f"{runtime:.2f}s")

        # Problem solver & 1-click fixes if not feasible
        diag = st.session_state.get("infeasibility_diagnosis")
        if result.status not in ("OPTIMAL", "FEASIBLE") and diag is not None:
            st.divider()
            st.subheader("🤖 Seating Problem Solver & Quick Fixes")
            st.error(f"**What Happened**: {diag.summary}")

            with st.expander("🔍 Details on What Caused the Problem", expanded=True):
                for issue in diag.issues:
                    st.markdown(f"#### ⚠️ {issue.title}")
                    st.write(issue.description)

            if diag.batch_metrics:
                st.markdown("#### 📊 Student Count by Branch vs Safe Room Space")
                batch_df = pd.DataFrame([
                    {
                        "Branch": b.batch,
                        "Students": b.student_count,
                        "Safe Branch Limit": b.max_independent_capacity,
                        "Space Used": f"{b.utilization_pct}%",
                        "Status": "❌ Over Limit" if b.is_bottleneck else "✅ Fits Safely",
                    }
                    for b in diag.batch_metrics
                ])
                st.dataframe(batch_df, use_container_width=True, hide_index=True)

            if diag.remediations:
                st.subheader("💡 1-Click Quick Fixes")
                st.markdown("Pick any solution below to easily fix the seating issue and create the plan:")

                for i, rem in enumerate(diag.remediations):
                    with st.container(border=True):
                        rem_col1, rem_col2 = st.columns([3, 1])
                        with rem_col1:
                            st.markdown(f"**{rem.title}** · *{rem.confidence_score}% Success Chance*")
                            st.caption(rem.description)
                            if rem.trade_off:
                                st.caption(f"**What to keep in mind:** *{rem.trade_off}*")
                            st.info(f"**Benefit:** {rem.impact}")

                        with rem_col2:
                            if rem.action_type == "relax_adjacency":
                                if st.button("⚡ Apply & Re-solve", key=f"rem_btn_{i}", type="primary"):
                                    st.session_state["confirmed_nl_config"] = st.session_state.get("confirmed_nl_config", {})
                                    st.session_state["confirmed_nl_config"]["adjacency_mode"] = rem.payload.get("target_adjacency", "horizontal")
                                    st.rerun()

                            elif rem.action_type == "increase_time":
                                if st.button("⏱️ Increase & Re-solve", key=f"rem_btn_{i}", type="primary"):
                                    st.session_state["confirmed_nl_config"] = st.session_state.get("confirmed_nl_config", {})
                                    st.session_state["confirmed_nl_config"]["solver_time_limit_seconds"] = rem.payload.get("time_limit", 120)
                                    st.rerun()

                            elif rem.action_type == "activate_room":
                                if st.button("⚡ Activate & Re-solve", key=f"rem_btn_{i}", type="primary"):
                                    with get_db_session() as db:
                                        success, msg, ctx = apply_negotiation_proposal(rem.id, db)
                                        if success:
                                            st.success(msg)
                                            st.rerun()
                                        else:
                                            st.error(msg)

        # Assignment table and CSV export if assignments exist
        if result.assignments:
            st.divider()
            st.subheader("Generated Seat Assignments")

            df = pd.DataFrame(result.assignments)
            st.caption(f"Total assignment records: {len(df)}. Showing first 50 records below:")
            st.dataframe(df.head(50), use_container_width=True, hide_index=True)

            csv_data = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Download Full Assignment CSV",
                data=csv_data,
                file_name="seating_assignments.csv",
                mime="text/csv",
                use_container_width=True,
            )

    else:
        with st.container(border=True):
            st.info("No seating plan has been generated in this session yet.")
            st.markdown(
                "1. Review the solver settings above.\n"
                "2. Click **'🤖 Quick Check: Will Students Fit?'** to test desk space.\n"
                "3. Click **'🚀 Create Seating Plan'** to generate your plan.\n"
                "4. Download your CSV assignments or explore the other tabs above."
            )


# ==================================================
# TAB 2: TEST SCENARIOS ('WHAT-IF')
# ==================================================
with tab_what_if:
    st.subheader("🔮 Test More Students or Closed Classrooms")
    st.markdown(
        "Try out different situations before exam day. "
        "See what happens if more students register or if any classroom is closed for maintenance—without changing any real data."
    )

    sim_students_base = all_students_base
    sim_all_layouts = all_rooms_list
    total_base_students = len(sim_students_base)

    sim_col1, sim_col2 = st.columns([1, 1])

    with sim_col1:
        mult = st.slider(
            "Change Student Numbers",
            min_value=0.5,
            max_value=3.0,
            value=1.0,
            step=0.1,
            format="%.1fx",
            help="Test with fewer or more students.",
            key="sim_slider_tab2",
        )
        sim_students_est = max(1, int(total_base_students * mult))
        st.caption(f"Testing with **{sim_students_est} students** (current: {total_base_students})")

    with sim_col2:
        sim_mode = st.selectbox(
            "Spacing Rule to Test",
            options=["horizontal_vertical", "horizontal"],
            format_func=lambda x: "Strict Spacing (Skip next seat & row)" if x == "horizontal_vertical" else "Normal Spacing (Skip side-by-side seat only)",
            key="sim_mode_tab2",
        )

    all_room_ids = [lay.room_id for lay in sim_all_layouts]
    disabled_rooms = st.multiselect(
        "Simulate Classroom Closures (Repairs / Painting / Closed)",
        options=all_room_ids,
        default=[],
        help="Pick any classrooms you want to pretend are closed.",
        key="sim_disabled_tab2",
    )

    sim_result = simulate_what_if_scenario(
        students=sim_students_base,
        layouts=sim_all_layouts,
        student_multiplier=mult,
        disabled_room_ids=disabled_rooms,
        adjacency_mode=sim_mode,
    )

    st.markdown("---")
    st.subheader("Test Results")

    sim_m1, sim_m2, sim_m3, sim_m4 = st.columns(4)
    with sim_m1:
        st.metric("Test Students", sim_result["sim_students_count"])
    with sim_m2:
        st.metric("Available Desks", sim_result["sim_seats_count"])
    with sim_m3:
        margin = sim_result["seat_surplus"] if sim_result["seat_surplus"] > 0 else -sim_result["seat_deficit"]
        st.metric(
            "Extra or Missing Desks",
            f"{abs(margin)} desks",
            delta="Extra desks" if margin >= 0 else "Need more desks",
            delta_color="normal" if margin >= 0 else "inverse",
        )
    with sim_m4:
        st.metric(
            "Will They Fit?",
            "✅ All Fit" if sim_result["is_feasible"] else "❌ Need More Space",
        )

    util_ratio = min(1.0, sim_result["sim_students_count"] / max(1, sim_result["sim_seats_count"]))
    st.progress(
        util_ratio,
        text=f"Desk Usage: {round(util_ratio * 100, 1)}% ({sim_result['sim_students_count']} / {sim_result['sim_seats_count']} desks used)",
    )

    if sim_result["bottlenecks"]:
        st.warning("⚠️ **These branches will need more space:**")
        for b in sim_result["bottlenecks"]:
            st.markdown(
                f"- Branch **`{b['batch']}`**: {b['count']} students is more than the {b['max_cap']} safe desks available (need {b['deficit']} more desks)."
            )


# ==================================================
# TAB 3: ROOM CAPACITY GUIDE
# ==================================================
with tab_capacity:
    st.subheader("📐 Classroom Desk Capacity Guide")
    st.markdown(
        "To prevent copying during exams, students in the same class cannot sit right next to each other. "
        "Because of this empty desk rule, each room safely holds about half its total desks for students from the same branch."
    )

    cap_layouts = all_rooms_list
    analysis_data = get_classroom_checkerboard_analysis(cap_layouts)
    if analysis_data:
        geo_df = pd.DataFrame([
            {
                "Classroom": item["room_id"],
                "Room Name": item["room_name"],
                "Desk Grid": f"{item['rows']} rows × {item['columns']} cols",
                "Total Desks": item["total_seats"],
                "Usable Desks": item["usable_seats"],
                "Max per Branch (Strict Spacing)": item["max_single_batch_hv"],
                "Max per Branch (Normal Spacing)": item["max_single_batch_h"],
                "Status": "🟢 Open" if item["is_available"] else "⚪ Closed",
            }
            for item in analysis_data
        ])
        st.dataframe(geo_df, use_container_width=True, hide_index=True)

        st.info(
            "💡 **How to read this table**: If a room has 30 usable desks, at most 15 students from the same branch "
            "can sit in that room under strict spacing so that no two classmates sit next to or directly behind each other."
        )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.divider()
st.caption("EXAMFLOW · Seating Generation · Fast Conflict-Free Optimization")
