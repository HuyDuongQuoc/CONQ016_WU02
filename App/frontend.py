import streamlit as st
import pandas as pd
import calendar
import sys
from datetime import datetime
from pathlib import Path
import plotly.express as px

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ga_engine.api import optimize_tasks

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
        min-height: 35px;
        font-size: 17px;
        font-weight: 500;
        line-height: 1.45;
        white-space: normal;
        overflow-wrap: anywhere;
        word-break: break-word;
    }
    </style>
""", unsafe_allow_html=True)

# Header chính của Dashboard
st.markdown('<div class="main-header">PROJECT: SMART TIMETABLE & TASK OPTIMIZER - STUDENT DASHBOARD</div>', unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load_and_optimize_tasks() -> tuple[pd.DataFrame, pd.DataFrame]:
    data_path = PROJECT_ROOT / "Data" / "df_500.csv"
    source_df = pd.read_csv(data_path)
    result = optimize_tasks(source_df)
    gantt_df = result["gantt_df"].copy()
    history_df = result["history_df"].copy()
    return gantt_df, history_df


try:
    gantt_df, history_df = load_and_optimize_tasks()
except Exception as exc:
    st.error(f"Cannot load optimization data: {exc}")
    st.stop()

gantt_df["end"] = pd.to_datetime(gantt_df["end"], errors="coerce")
gantt_df = gantt_df.dropna(subset=["end", "task_name"]).copy()

priority_rank_df = gantt_df.sort_values(by=["end", "task_name"]).drop_duplicates(subset=["task_name"])
project_names = priority_rank_df["task_name"].tolist()
project_priority = {name: f"P{idx + 1}" for idx, name in enumerate(project_names)}

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

    event_map = {}
    month_df = gantt_df[gantt_df["end"].dt.month == selected_month]
    for _, row in month_df.iterrows():
        end_day = int(row["end"].day)
        title = f"{row['task_name']} (End: {row['end'].strftime('%d/%m')})"
        priority = project_priority.get(str(row["task_name"]), "P3")
        color = "#f56565" if priority == "P1" else "#ed8936" if priority == "P2" else "#4299e1"
        event_map.setdefault(end_day, []).append((title, color))

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


# ================= (LEFT COLUMN) =================
with col_left:
    st.markdown('<div class="section-header">PRIORITIZED TASK LIST & DETAILS</div>', unsafe_allow_html=True)

    today = datetime.now().date()
    upcoming_priority_rank_df = priority_rank_df[priority_rank_df["end"].dt.date > today]

    project_cards = []
    for index, (_, row) in enumerate(upcoming_priority_rank_df.iterrows()):
        project_name = str(row["task_name"])
        checkbox_key = f"finished::{project_name}"
        if checkbox_key not in st.session_state:
            st.session_state[checkbox_key] = False

        # Time remaining to deadline in hours
        hours_left = (row["end"] - datetime.now()).total_seconds() / 3600

        if hours_left < 24:
            deadline_color = "🔴"
        elif hours_left <= 48:
            deadline_color = "🟠"
        else:
            deadline_color = "🟢"

        project_cards.append(
            {
                "priority": project_priority[project_name],
                "color": deadline_color,
                "title": f"{project_name}",
                "checkbox_key": checkbox_key,
                "is_finished": st.session_state[checkbox_key],
                "sort_order": index,
            }
        )

    project_cards = sorted(project_cards, key=lambda task: (task["is_finished"], task["sort_order"]))

    if not project_cards:
        st.info("No upcoming projects after today.")
    else:
        for task in project_cards:
            with st.container(border=True):
                checkbox_col, title_col = st.columns([1, 11], gap="small")
                with checkbox_col:
                    st.checkbox("Mark as finished", key=task["checkbox_key"], label_visibility="collapsed")
                with title_col:
                    st.markdown(
                        f"<div class='task-box-title'>{task['color']} [{task['priority']}] {task['title']}</div>",
                        unsafe_allow_html=True,
                    )