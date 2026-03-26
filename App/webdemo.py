import io
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
from ga_engine.config import GAConfig
from Data.data_preprocessing import CSVTaskProcessor

# 1. CẤU HÌNH TRANG VÀ CSS TÙY CHỈNH
st.set_page_config(page_title="Smart Timetable & Task Optimizer", layout="wide")

# CSS để tùy chỉnh màu sắc và giao diện (Đã cập nhật theo yêu cầu Minimalist)
st.markdown("""
    <style>
    /* Đổi màu Header sang Xám Đen nhám */
    .main-header {
        background-color: #1F2937; 
        color: white;
        padding: 15px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 24px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .section-header {
        background-color: #1F2937;
        color: white;
        padding: 12px 15px;
        border-radius: 8px;
        font-weight: 600;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .task-box-title {
        display: flex;
        align-items: center;
        min-height: 35px;
        font-size: 16px;
        font-weight: 500;
        line-height: 1.45;
        white-space: normal;
        overflow-wrap: anywhere;
        word-break: break-word;
    }
    
    /* Hiệu ứng hover đổ bóng cho Task Card ở cột trái */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.task-box-title) {
        transition: all 0.3s ease;
        border-radius: 8px;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.task-box-title):hover {
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
        border-color: #cbd5e1;
    }
    
    /* Tùy chỉnh Metrics */
    div[data-testid="stMetricValue"] {
        font-size: 28px !important;
        color: #1F2937;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🚀 PROJECT: SMART TIMETABLE & TASK OPTIMIZER - DASHBOARD</div>', unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def preprocess_and_optimize_tasks(uploaded_csv_bytes: bytes) -> tuple[pd.DataFrame, pd.DataFrame]:
    now = datetime.now()
    temp_csv_path = PROJECT_ROOT / "Data" / "_uploaded_temp.csv"

    pd.read_csv(io.BytesIO(uploaded_csv_bytes)).to_csv(temp_csv_path, index=False)

    processor = CSVTaskProcessor(now=now)
    processed_df = processor.process_csv(str(temp_csv_path))

    config = GAConfig(now=now, population_size=30, generations=40, mutation_rate=0.15)
    result = optimize_tasks(processed_df, config=config)
    gantt_df = result["gantt_df"].copy()
    history_df = result["history_df"].copy()
    return gantt_df, history_df

# --- HÀM ĐỒNG BỘ MÀU SẮC (PASTEL) ---
def get_task_urgency_color(end_date):
    """Tính toán màu sắc dựa trên thời gian còn lại đến deadline"""
    hours_left = (end_date - datetime.now()).total_seconds() / 3600
    if hours_left < 72:      # Gấp (< 3 ngày)
        return "#FCA5A5"     # Đỏ nhạt pastel
    elif hours_left <= 168:  # Vừa (< 7 ngày)
        return "#FDE047"     # Vàng nhạt pastel
    else:                    # Chill
        return "#86EFAC"     # Xanh lá lợt pastel

uploaded_file = st.file_uploader(
    "Upload data file (.csv)",
    type=["csv"],
    key="task_csv_uploader",
    help="Upload your task dataset, then the app will optimize and display results."
)

if uploaded_file is not None:
    st.session_state["uploaded_csv_name"] = uploaded_file.name
    st.session_state["uploaded_csv_bytes"] = uploaded_file.getvalue()

uploaded_csv_bytes = st.session_state.get("uploaded_csv_bytes")

if uploaded_csv_bytes is None:
    st.info("Please upload a CSV file to run task optimization.")
    st.stop()

try:
    gantt_df, history_df = preprocess_and_optimize_tasks(uploaded_csv_bytes)
except Exception as exc:
    st.error(f"Cannot process uploaded file: {exc}")
    st.stop()

gantt_df["end"] = pd.to_datetime(gantt_df["end"], errors="coerce")
gantt_df = gantt_df.dropna(subset=["end", "task_name"]).copy()

priority_rank_df = gantt_df.sort_values(by=["end", "task_name"]).drop_duplicates(subset=["task_name"])
project_names = priority_rank_df["task_name"].tolist()
project_priority = {name: f"P{idx + 1}" for idx, name in enumerate(project_names)}

# Khởi tạo trạng thái hoàn thành cho các task
for name in project_names:
    key = f"finished::{name}"
    if key not in st.session_state:
        st.session_state[key] = False

# ================= (METRICS - THỐNG KÊ) =================
total_tasks = len(project_names)
completed_tasks = sum(1 for name in project_names if st.session_state[f"finished::{name}"])
pending_tasks = total_tasks - completed_tasks

m_col1, m_col2, m_col3 = st.columns(3)
m_col1.metric("📌 Tổng số Task", total_tasks)
m_col2.metric("✅ Đã hoàn thành", completed_tasks)
m_col3.metric("🔥 Cần xử lý", pending_tasks)

st.divider() # Đường kẻ ngang phân cách

# 2. CHIA BỐ CỤC GIAO DIỆN 
col_left, col_right = st.columns([1, 2], gap="large")

# ================= (RIGHT COLUMN: CALENDAR) =================
with col_right:
    st.markdown('<div class="section-header">📅 CALENDAR: TASK DEADLINES</div>', unsafe_allow_html=True)

    current_year = datetime.now().year
    month_names = list(calendar.month_name[1:])
    selected_month_name = st.selectbox(
        "Select month",
        month_names,
        index=datetime.now().month - 1,
        key="calendar_month_selector",
        label_visibility="collapsed"
    )
    selected_month = month_names.index(selected_month_name) + 1

    event_map = {}
    month_df = gantt_df[gantt_df["end"].dt.month == selected_month]
    for _, row in month_df.iterrows():
        end_day = int(row["end"].day)
        title = f"{row['task_name']}"
        # Đồng bộ lấy màu từ hàm chung
        color = get_task_urgency_color(row["end"]) 
        event_map.setdefault(end_day, []).append((title, color))

    week_rows = calendar.Calendar(firstweekday=6).monthdatescalendar(current_year, selected_month)
    dynamic_height = len(week_rows) * 90 + 130 # Tính chiều cao động cho cột trái

    calendar_rows_html = []
    for week in week_rows:
        cells = []
        for day_obj in week:
            is_current_month = day_obj.month == selected_month
            day_number_color = "#1F2937" if is_current_month else "#9CA3AF"
            day_events = event_map.get(day_obj.day, []) if is_current_month else []

            badges_html = ""
            for title, color in day_events:
                # Chữ đổi sang Xám đen (#1F2937) để nổi bật trên nền Pastel
                badges_html += (
                    f"<div style='margin-top:4px; background-color:{color}; color:#1F2937; "
                    f"padding:3px 6px; border-radius:4px; font-size:11px; font-weight:600; "
                    f"white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{title}</div>"
                )

            # Đổi màu viền td sang xám nhạt #E5E7EB
            cells.append(
                f"<td style='border:1px solid #E5E7EB; height:90px; vertical-align:top; padding:8px; "
                f"background-color:#ffffff; transition: background-color 0.2s;'>"
                f"<span style='color:{day_number_color}; font-weight:500;'>{day_obj.day}</span>{badges_html}</td>"
            )
        calendar_rows_html.append(f"<tr>{''.join(cells)}</tr>")

    # Bọc Table trong một div để bo tròn góc tổng thể
    calendar_html = f"""
    <div style="border-radius: 10px; overflow: hidden; border: 1px solid #E5E7EB; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
        <table style="width:100%; text-align:left; border-collapse:collapse; table-layout:fixed; margin:0;">
            <tr style="background-color:#F9FAFB; text-align:center; font-weight:600; color:#4B5563;">
                <th style="border:1px solid #E5E7EB; padding:10px;">Sun</th>
                <th style="border:1px solid #E5E7EB; padding:10px;">Mon</th>
                <th style="border:1px solid #E5E7EB; padding:10px;">Tue</th>
                <th style="border:1px solid #E5E7EB; padding:10px;">Wed</th>
                <th style="border:1px solid #E5E7EB; padding:10px;">Thu</th>
                <th style="border:1px solid #E5E7EB; padding:10px;">Fri</th>
                <th style="border:1px solid #E5E7EB; padding:10px;">Sat</th>
            </tr>
            {''.join(calendar_rows_html)}
        </table>
    </div>
    <br>
    """
    st.markdown(calendar_html, unsafe_allow_html=True)


# ================= (LEFT COLUMN: TASK LIST) =================
with col_left:
    st.markdown('<div class="section-header">🎯 PRIORITIZED TASKS</div>', unsafe_allow_html=True)

    today = datetime.now().date()
    upcoming_priority_rank_df = priority_rank_df[priority_rank_df["end"].dt.date >= today]

    project_cards = []
    for index, (_, row) in enumerate(upcoming_priority_rank_df.iterrows()):
        project_name = str(row["task_name"])
        checkbox_key = f"finished::{project_name}"
        
        # Đồng bộ màu sắc với Calendar
        color_hex = get_task_urgency_color(row["end"])

        project_cards.append(
            {
                "priority": project_priority[project_name],
                "color": color_hex,
                "title": f"{project_name}",
                "checkbox_key": checkbox_key,
                "is_finished": st.session_state[checkbox_key],
                "sort_order": index,
            }
        )

    project_cards = sorted(project_cards, key=lambda task: (task["is_finished"], task["sort_order"]))

    if not project_cards:
        st.info("🎉 You have cleared all upcoming tasks!")
    else:
        # Bọc thanh cuộn với chiều cao linh động bằng với lịch bên phải
        with st.container(height=dynamic_height):
            for task in project_cards:
                with st.container(border=True):
                    checkbox_col, title_col = st.columns([1, 10], gap="small")
                    with checkbox_col:
                        st.checkbox("Done", key=task["checkbox_key"], label_visibility="collapsed")
                    with title_col:
                        # Dùng vòng tròn màu (circle) đồng bộ 100% với màu bên Calendar thay vì Emoji
                        st.markdown(
                            f"<div class='task-box-title'>"
                            f"<span style='display:inline-block; width:14px; height:14px; border-radius:50%; "
                            f"background-color:{task['color']}; margin-right:8px; border: 1px solid rgba(0,0,0,0.1);'></span>"
                            f"<b>[{task['priority']}]</b>&nbsp; {task['title']}</div>",
                            unsafe_allow_html=True,
                        )