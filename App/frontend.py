import streamlit as st
import pandas as pd
import numpy as np
import calendar
from datetime import datetime
import plotly.express as px

# 1. CẤU HÌNH TRANG VÀ CSS TÙY CHỈNH
st.set_page_config(page_title="Smart Timetable & Task Optimizer", layout="wide")

# CSS để tùy chỉnh màu sắc và giao diện cho giống với thiết kế
st.markdown("""
    <style>
    .main-header {
        background-color: #2b6cb0;
        color: white;
        padding: 15px;
        border-radius: 5px;
        font-weight: bold;
        font-size: 24px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
    }
    .section-header {
        background-color: #2b6cb0;
        color: white;
        padding: 10px;
        border-radius: 5px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .task-box-title {
        align-items: center;
        # min-height: 35px;
        font-size: 17px;
        font-weight: 500;
        line-height: 1;
    }
    /* Checkbox checked state for mini tasks */
    [data-testid="stCheckbox"] [role="checkbox"][aria-checked="true"] {
        background-color: #5adb6b ;
        border-color: #5adb6b ;
    }
    </style>
""", unsafe_allow_html=True)

# Header chính của Dashboard
st.markdown('<div class="main-header">PROJECT: SMART TIMETABLE & TASK OPTIMIZER - STUDENT DASHBOARD</div>', unsafe_allow_html=True)

# 2. CHIA BỐ CỤC GIAO DIỆN 
col_left, col_right = st.columns([1, 2], gap="large")

# ================= (RIGHT COLUMN) =================
with col_right:
    # --- BẢNG CALENDAR ---
    st.markdown('<div class="section-header">CALENDAR: TASK DEADLINES</div>', unsafe_allow_html=True)

    current_year = datetime.now().year
    month_names = list(calendar.month_name[1:])
    selected_month_name = st.selectbox(
        "Select month",
        month_names,
        index=datetime.now().month - 1,
        key="calendar_month_selector"
    )
    selected_month = month_names.index(selected_month_name) + 1

    # HARDCODE DATA : DEALINE
    monthly_events = {
        1: [(5, "Math Assignment", "#4299e1"), (12, "Physics Quiz", "#48bb78"), (20, "History Essay", "#9f7aea")],
        2: [(4, "Math Assignment", "#4299e1"), (10, "Physics Quiz", "#48bb78"), (18, "ML Project Report", "#4299e1")],
        3: [(3, "Math Assignment", "#4299e1"), (9, "Physics Quiz", "#48bb78"), (22, "History Essay", "#9f7aea")],
        4: [(1, "Math Assignment", "#4299e1"), (3, "Physics Quiz", "#48bb78"), (4, "History Essay", "#9f7aea"), (9, "ML Project Report", "#4299e1"), (10, "Math Assignment", "#f56565")],
        5: [(6, "Math Assignment", "#4299e1"), (14, "Physics Quiz", "#48bb78"), (24, "History Essay", "#9f7aea")],
        6: [(2, "Math Assignment", "#4299e1"), (11, "Physics Quiz", "#48bb78"), (19, "ML Project Report", "#4299e1")],
        7: [(8, "Math Assignment", "#4299e1"), (15, "Physics Quiz", "#48bb78"), (28, "History Essay", "#9f7aea")],
        8: [(5, "Math Assignment", "#4299e1"), (16, "Physics Quiz", "#48bb78"), (25, "ML Project Report", "#4299e1")],
        9: [(4, "Math Assignment", "#4299e1"), (13, "Physics Quiz", "#48bb78"), (26, "History Essay", "#9f7aea")],
        10: [(7, "Math Assignment", "#4299e1"), (17, "Physics Quiz", "#48bb78"), (23, "ML Project Report", "#4299e1")],
        11: [(6, "Math Assignment", "#4299e1"), (12, "Physics Quiz", "#48bb78"), (21, "History Essay", "#9f7aea")],
        12: [(3, "Math Assignment", "#4299e1"), (11, "Physics Quiz", "#48bb78"), (20, "ML Project Report", "#4299e1")],
    }

    event_map = {}
    for day, title, color in monthly_events.get(selected_month, []):
        event_map.setdefault(day, []).append((title, color))

    week_rows = calendar.Calendar(firstweekday=6).monthdatescalendar(current_year, selected_month)

    calendar_rows_html = []
    for week in week_rows:
        cells = []
        for day_obj in week:
            is_current_month = day_obj.month == selected_month
            day_number_color = "#4a5568" if is_current_month else "#a0aec0"
            day_events = event_map.get(day_obj.day, []) if is_current_month else []

            badges_html = ""
            for title, color in day_events:
                badges_html += (
                    f"<br><span style='display:inline-block; margin-top:3px; "
                    f"background-color:{color}; color:white; padding:2px 6px; "
                    f"border-radius:4px; font-size:12px;'>{title}</span>"
                )

            cells.append(
                f"<td style='border:1px solid #e2e8f0; height:90px; vertical-align:top; padding:6px; "
                f"background-color:#ffffff;'>"
                f"<span style='color:{day_number_color};'>{day_obj.day}</span>{badges_html}</td>"
            )
        calendar_rows_html.append(f"<tr>{''.join(cells)}</tr>")

    calendar_html = f"""
    <table style="width:100%; text-align:left; border-collapse:collapse; table-layout:fixed;">
        <tr style="background-color:#f7fafc; text-align:center; font-weight:bold;">
            <th style="border:1px solid #e2e8f0; padding:8px;">Sun</th>
            <th style="border:1px solid #e2e8f0; padding:8px;">Mon</th>
            <th style="border:1px solid #e2e8f0; padding:8px;">Tue</th>
            <th style="border:1px solid #e2e8f0; padding:8px;">Wed</th>
            <th style="border:1px solid #e2e8f0; padding:8px;">Thu</th>
            <th style="border:1px solid #e2e8f0; padding:8px;">Fri</th>
            <th style="border:1px solid #e2e8f0; padding:8px;">Sat</th>
        </tr>
        {''.join(calendar_rows_html)}
    </table>
    <br>
    """
    st.markdown(calendar_html, unsafe_allow_html=True)

    # --- BIỂU ĐỒ MONTHLY PROGRESS ---
    st.markdown('<div class="section-header">MONTHLY PROGRESS: COMPLETED TASKS</div>', unsafe_allow_html=True)
    
    days_in_month = calendar.monthrange(current_year, selected_month)[1]
    days = np.arange(1, days_in_month + 1)
    
    # HARDCODE DATA: SỐ TASK HOÀN THÀNH MỖI NGÀY (DÙNG SEED THEO THÁNG ĐỂ DỮ LIỆU ỔN ĐỊNH KHI RERUN)
    # Dùng seed theo tháng để dữ liệu ổn định khi rerun
    rng = np.random.default_rng(seed=selected_month)
    completed_tasks = rng.integers(0, 5, size=days_in_month)
    
    chart_data = pd.DataFrame({
        'Day': days,
        'Completed Tasks': completed_tasks
    })
    
    # Dùng plotly bar_chart để tạo biểu đồ cột với nhãn x xoay dọc
    fig = px.bar(chart_data, x='Day', y='Completed Tasks', 
                 color_discrete_sequence=["#99d4fb"],
                 labels={'Completed Tasks': 'Completed Tasks', 'Day': 'Day'})
    fig.update_layout(
        showlegend=False,
        height=400,
        margin=dict(b=100)
    )
    st.plotly_chart(fig, use_container_width=True)

# ================= (LEFT COLUMN) =================
with col_left:
    header_text_col, header_add_col = st.columns([8, 1.5])
    with header_text_col:
        st.markdown('<div class="section-header">PRIORITIZED TASK LIST & DETAILS</div>', unsafe_allow_html=True)

    with header_add_col:
        if st.button("Add", key="open_add_task_btn", help="Add task"):
            st.session_state.show_add_task_input = True
            st.rerun()

    # HARDCODE DATA: LIST OF PROJJECT
    default_tasks = [
        {
            "priority": "P1",
            "color": "🟢",
            "title": "Finish ML Project",
            "expanded": True,
            "subtasks": [
                {"name": "Data Collection", "done": True},
                {"name": "Feature Engineering", "done": False},
                {"name": "Model Training", "done": False},
                {"name": "Write Report", "done": False},
            ],
        },
        {"priority": "P2", "color": "🔴", "title": "Prepare for Final Exams", "expanded": False, "subtasks": []},
        {"priority": "P3", "color": "🟠", "title": "Physics Assignment", "expanded": False, "subtasks": []},
        {"priority": "P2", "color": "🟡", "title": "Finish Microenooting", "expanded": False, "subtasks": []},
        {"priority": "P2", "color": "🟡", "title": "P1: Poster Final Exams", "expanded": False, "subtasks": []},
        {"priority": "P3", "color": "🟡", "title": "P1: Finish ML Project", "expanded": False, "subtasks": []},
    ]

    if "tasks_data" not in st.session_state:
        st.session_state.tasks_data = default_tasks
    if "show_add_task_input" not in st.session_state:
        st.session_state.show_add_task_input = False
    if "new_task_input_nonce" not in st.session_state:
        st.session_state.new_task_input_nonce = 0

    if st.session_state.show_add_task_input:
        new_task_key = f"new_task_title_{st.session_state.new_task_input_nonce}"
        new_task_title = st.text_input(
            "Task title",
            placeholder="Enter a new task title...",
            key=new_task_key,
        )
        add_task_col, cancel_task_col = st.columns(2)
        with add_task_col:
            if st.button("Add Task", key="confirm_add_task_btn"):
                task_title = new_task_title.strip()
                if task_title:
                    st.session_state.tasks_data.append(
                        {
                            "priority": "P3",
                            "color": "🟡",
                            "title": task_title,
                            "expanded": True,
                            "subtasks": [],
                        }
                    )
                    st.session_state.show_add_task_input = False
                    st.session_state.new_task_input_nonce += 1
                    st.rerun()
                else:
                    st.warning("Please enter a task title before adding.")
        with cancel_task_col:
            if st.button("Cancel", key="cancel_add_task_btn"):
                st.session_state.show_add_task_input = False
                st.session_state.new_task_input_nonce += 1
                st.rerun()

    # Render task boxes with custom header row
    for task_idx, task in enumerate(st.session_state.tasks_data):
        expanded_key = f"task_expanded_{task_idx}"
        if expanded_key not in st.session_state:
            st.session_state[expanded_key] = task["expanded"]

        with st.container(border=True):
            toggle_col, title_col, task_add_col = st.columns([1, 8, 1.5], vertical_alignment="center" )

            with toggle_col:
                toggle_icon = "▾" if st.session_state[expanded_key] else "▸"
                if st.button(
                    toggle_icon,
                    key=f"toggle_task_btn_{task_idx}",
                    help="Expand/Collapse",
                    type="tertiary",
                ):
                    st.session_state[expanded_key] = not st.session_state[expanded_key]
                    st.rerun()

            with title_col:
                st.markdown(
                    f"<div class='task-box-title'>{task['color']} [{task['priority']}] {task['title']}</div>" ,
                    unsafe_allow_html=True,
                )

            show_add_key = f"show_add_input_{task_idx}"
            nonce_key = f"new_subtask_input_nonce_{task_idx}"
            if show_add_key not in st.session_state:
                st.session_state[show_add_key] = False
            if nonce_key not in st.session_state:
                st.session_state[nonce_key] = 0

            with task_add_col:
                if st.button("➕", key=f"open_add_subtask_btn_{task_idx}", help="Add mini task"):
                    st.session_state[show_add_key] = True
                    st.rerun()

            if not st.session_state[expanded_key]:
                continue

            if st.session_state[show_add_key]:
                input_key = f"new_subtask_input_{task_idx}_{st.session_state[nonce_key]}"
                st.text_input(
                    "Mini task",
                    placeholder="Enter a new mini task...",
                    key=input_key,
                    label_visibility="collapsed",
                )

                add_col, cancel_col = st.columns(2)
                with add_col:
                    if st.button("Add", key=f"confirm_add_subtask_btn_{task_idx}"):
                        new_subtask_name = st.session_state.get(input_key, "").strip()
                        if new_subtask_name:
                            st.session_state.tasks_data[task_idx]["subtasks"].append(
                                {"name": new_subtask_name, "done": False}
                            )
                            st.session_state[show_add_key] = False
                            st.session_state[nonce_key] += 1
                            st.rerun()
                        else:
                            st.warning("Please enter a mini task name before adding.")

                with cancel_col:
                    if st.button("Cancel", key=f"cancel_add_subtask_btn_{task_idx}"):
                        st.session_state[show_add_key] = False
                        st.session_state[nonce_key] += 1
                        st.rerun()

            if task["subtasks"]:
                for sub_idx, subtask in enumerate(task["subtasks"]):
                    checkbox_key = f"task_{task_idx}_subtask_{sub_idx}_done"
                    if checkbox_key not in st.session_state:
                        st.session_state[checkbox_key] = subtask["done"]

                    done = st.checkbox(f"{subtask['name']}", key=checkbox_key)
                    st.session_state.tasks_data[task_idx]["subtasks"][sub_idx]["done"] = done
            else:
                st.write("No mini tasks have been assigned yet.")