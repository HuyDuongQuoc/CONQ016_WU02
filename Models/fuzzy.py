# models/fuzzy.py
import datetime
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

def calculate_urgency_score(hours_remaining, priority_level, cognitive_load, duration_mins):
    """
    Tính toán điểm khẩn cấp (0-10) dựa trên công thức Trọng số phân bổ.
    - hours_remaining: Số giờ tính từ hiện tại đến deadline (float/int)
    - priority_level: 1 (Low), 2 (Medium), 3 (High)
    - cognitive_load: 1 đến 10
    - duration_mins: Thời gian ước tính hoàn thành (int)
    """
    # 1. Xử lý ngoại lệ: Đã quá hạn hoặc không còn đủ thời gian để làm
    if hours_remaining <= 0 or (duration_mins / 60.0) >= hours_remaining:
        return 10.0
        
    # 2. Tính toán Yếu tố Áp lực thời gian (Thang 10)
    time_pressure_ratio = duration_mins / (hours_remaining * 60.0)
    tp_score = min(time_pressure_ratio * 10, 10.0) # Giới hạn tối đa là 10
    
    # 3. Tính toán Yếu tố Ưu tiên (Thang 10)
    pf_score = priority_level * 3.33
    
    # 4. Tính toán Yếu tố Nhận thức (Đã ở thang 10)
    cl_score = float(cognitive_load)
    
    # 5. Tổng hợp theo trọng số (Time: 50%, Priority: 30%, Cognitive: 20%)
    final_score = (0.5 * tp_score) + (0.3 * pf_score) + (0.2 * cl_score)
    
    # Đảm bảo kết quả cuối cùng không vượt quá 10
    return round(min(final_score, 10.0), 2)

def build_fuzzy_engine():
    """
    Khởi tạo Động cơ Suy luận Mờ (Fuzzy Inference Engine).
    Chỉ cần gọi hàm này 1 lần khi khởi động hệ thống để tránh tính toán lại.
    """
    # 1. KHAI BÁO BIẾN 
    # Dùng bước nhảy nhỏ (0.1 hoặc 1) để đồ thị mượt mà, giải mờ chính xác hơn
    time_left = ctrl.Antecedent(np.arange(0, 169, 1), 'time_left') # 0 đến 168 giờ (7 ngày)
    priority = ctrl.Antecedent(np.arange(1, 4, 1), 'priority')     # 1, 2, 3
    cog_load = ctrl.Antecedent(np.arange(1, 11, 0.1), 'cog_load')  # 1.0 đến 10.0
    
    urgency = ctrl.Consequent(np.arange(0, 10.1, 0.1), 'urgency')  # Điểm ra 0.0 đến 10.0

    # 2. ĐỊNH NGHĨA HÀM THÀNH VIÊN
    # Thời gian: Quá gấp (0-48h), Hơi gấp (24-72h), Thong thả (48-168h)
    time_left['qua_gap'] = fuzz.trapmf(time_left.universe, [0, 0, 24, 48])
    time_left['hoi_gap'] = fuzz.trimf(time_left.universe, [24, 48, 72])
    time_left['thong_tha'] = fuzz.trapmf(time_left.universe, [48, 72, 168, 168])

    # Mức độ ưu tiên: Thấp (1), Trung bình (2), Cao (3)
    priority['thap'] = fuzz.trimf(priority.universe, [1, 1, 2])
    priority['trung_binh'] = fuzz.trimf(priority.universe, [1, 2, 3])
    priority['cao'] = fuzz.trimf(priority.universe, [2, 3, 3])

    # Tải trọng nhận thức: Nhẹ (1-5), Vừa (3-8), Nặng (6-10)
    cog_load['nhe'] = fuzz.trapmf(cog_load.universe, [1, 1, 3, 5])
    cog_load['vua'] = fuzz.trimf(cog_load.universe, [3, 5.5, 8])
    cog_load['nang'] = fuzz.trapmf(cog_load.universe, [6, 8, 10, 10])

    # Độ khẩn cấp (Output): Thấp (0-4), Trung bình (3-7), Cao (6-9), Báo động (8-10)
    urgency['thap'] = fuzz.trapmf(urgency.universe, [0, 0, 2, 4])
    urgency['trung_binh'] = fuzz.trimf(urgency.universe, [3, 5, 7])
    urgency['cao'] = fuzz.trimf(urgency.universe, [6, 7.5, 9])
    urgency['bao_dong'] = fuzz.trapmf(urgency.universe, [8, 9, 10, 10])

    # 3. THIẾT LẬP Fuzzy Rules
    # (Gom nhóm các luật có cùng kết quả để code ngắn gọn và chạy nhanh hơn)
    
    # Nhóm BÁO ĐỘNG
    rule_bao_dong = ctrl.Rule(
        (priority['cao'] & time_left['qua_gap']) |
        (priority['cao'] & time_left['hoi_gap'] & cog_load['nang']) |
        (priority['trung_binh'] & time_left['qua_gap'] & cog_load['nang']),
        urgency['bao_dong']
    )

    # Nhóm CAO
    rule_cao = ctrl.Rule(
        (priority['cao'] & time_left['thong_tha'] & cog_load['nang']) |
        (priority['trung_binh'] & time_left['qua_gap'] & ~cog_load['nang']) | # Dấu ~ nghĩa là KHÔNG PHẢI
        (priority['thap'] & time_left['qua_gap'] & cog_load['nang']),
        urgency['cao']
    )

    # Nhóm TRUNG BÌNH
    rule_trung_binh = ctrl.Rule(
        (priority['trung_binh'] & time_left['hoi_gap'] & ~cog_load['nang']) |
        (priority['thap'] & time_left['qua_gap'] & ~cog_load['nang']),
        urgency['trung_binh']
    )

    # Nhóm THẤP (Các trường hợp thong thả và ưu tiên thấp)
    rule_thap = ctrl.Rule(
        (priority['thap'] & time_left['thong_tha']) |
        (priority['thap'] & time_left['hoi_gap'] & cog_load['nhe']),
        urgency['thap']
    )

    # 4. TẠO HỆ THỐNG ĐIỀU KHIỂN
    urgency_ctrl = ctrl.ControlSystem([rule_bao_dong, rule_cao, rule_trung_binh, rule_thap])
    urgency_sim = ctrl.ControlSystemSimulation(urgency_ctrl)
    
    return urgency_sim

def evaluate_and_sort_tasks(task_list, fuzzy_sim):
    """
    Tính điểm Urgency cho một danh sách task và sắp xếp thứ tự ưu tiên.
    task_list: List các dictionary chứa thông tin task.
    fuzzy_sim: Động cơ mô phỏng Fuzzy đã khởi tạo.
    """
    for task in task_list:
        # Xử lý ngoại lệ cứng: Trễ hạn hoặc sát nút
        if task['hours_remaining'] <= 0 or (task['duration_mins'] / 60.0) >= task['hours_remaining']:
            task['urgency_score'] = 10.0
            continue
            
        # Đưa dữ liệu vào Động cơ Mờ
        fuzzy_sim.input['time_left'] = min(task['hours_remaining'], 168) # Giới hạn max 168h
        fuzzy_sim.input['priority'] = task['priority_level']
        fuzzy_sim.input['cog_load'] = task['cognitive_load']
        
        # Chạy suy luận và giải mờ (Defuzzification)
        try:
            fuzzy_sim.compute()
            task['urgency_score'] = round(fuzzy_sim.output['urgency'], 2)
        except ValueError:
            # Bắt lỗi nếu số liệu lọt ra ngoài vùng định nghĩa của đồ thị
            task['urgency_score'] = 5.0 

    # SẮP XẾP TIE-BREAKER: 
    # Ưu tiên 1: Khẩn cấp xếp trước
    # Ưu tiên 2: Deadline gần xếp trước
    # Ưu tiên 3: Task ngắn làm trước
    sorted_tasks = sorted(
        task_list,
        key=lambda x: (-x['urgency_score'], x['hours_remaining'], x['duration_mins'])
    )
    
    return sorted_tasks

# --- CHẠY THỬ KẾT QUẢ ---
if __name__ == "__main__":
    # Khởi tạo động cơ (Chỉ chạy 1 lần)
    engine = build_fuzzy_engine()
    
    # Mock data từ TV1 (Khoa)
    mock_tasks = [
        {"task_id": "T1", "task_name": "Code MIPS Lab", "hours_remaining": 12, "priority_level": 3, "cognitive_load": 9, "duration_mins": 180},
        {"task_id": "T2", "task_name": "Đọc Triết học", "hours_remaining": 12, "priority_level": 3, "cognitive_load": 5, "duration_mins": 60},
        {"task_id": "T3", "task_name": "Dọn dẹp file", "hours_remaining": 100, "priority_level": 1, "cognitive_load": 2, "duration_mins": 30}
    ]
    
    print("Đang xử lý phân luồng...\n")
    result = evaluate_and_sort_tasks(mock_tasks, engine)
    
    for idx, t in enumerate(result, 1):
        print(f"Top {idx}: [{t['urgency_score']}/10] {t['task_name']} | Cần {t['duration_mins']} phút")