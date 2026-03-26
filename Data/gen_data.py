from faker import Faker
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

fake = Faker()
# 1. Đọc file với dấu phẩy
# 2. names=['ID', 'Subject', 'Credits'] để đặt tên cho các cột
# 3. header=None để báo cho Pandas biết dòng đầu tiên là dữ liệu, không phải tiêu đề
df = pd.read_csv('Data/CS.csv', sep=',', names=['ID', 'Subject', 'Credits'], header=None)

print("DataFrame của bạn:")
print(df)

# Kiểm tra tổng tín chỉ
total_credits = df['Credits'].sum()
print(f"\nTong so tin chi: {total_credits}")

df = df.drop_duplicates()
prerequisites={
    'LA1005': ['LA1003'],
    'LA1007': ['LA1005'],
    'LA1009': ['LA1007'],
    'CO2001': ['CO1005'],
    'CO3005': ['CO1027'],
    'CO3015': ['CO1027'],
    'CO3041': ['CO3001'],
    'CO4337': ['CO335','CO4029'],

}

# 1. Tạo bộ tra cứu ID -> Tên môn
id_to_name = dict(zip(df['ID'], df['Subject']))

# 2. Hàm chuyển đổi: từ [ID1, ID2] thành [Name1, Name2]
def get_prereq_names(course_id):
    ids = prerequisites.get(course_id, [])
    # Tra cứu tên từng ID trong list, nếu không thấy thì giữ nguyên ID đó
    return [id_to_name.get(prereq_id, prereq_id) for prereq_id in ids]

# 3. Áp dụng vào DataFrame
df['Prerequisite_Names'] = df['ID'].apply(get_prereq_names)
df.to_csv('Data/CS1.csv', index=False)

def generate_fake_dataset(source_df, target_rows=500):
    new_data = []
    # DANH SÁCH MÔN CÓ 2 BTL (Ông thêm ID môn vào đây)
    subjects_with_2_btl = ['CO2001', 'CO3005', 'LA1007', 'CO1027'] 
    
    # Biến đếm để tạo hậu tố (suffix) tránh trùng ID khi lặp lại môn học
    iteration = 1
    
    while len(new_data) < target_rows:
        # Trộn ngẫu nhiên danh sách môn để data nhìn "tự nhiên" hơn
        shuffled_df = source_df.sample(frac=1).reset_index(drop=True)
        
        for _, row in shuffled_df.iterrows():
            if len(new_data) >= target_rows:
                break
                
            sub_id = row['ID']
            sub_name = row['Subject']
            # Hậu tố để phân biệt các lần gen (ví dụ: CO2001_v1, CO2001_v2)
            suffix = f"v{iteration}"
            
            # --- 1. TẠO 3 QUIZ (TUẦN TỰ) ---
            quiz_ids = []
            for i in range(1, 4):
                q_id = f"{sub_id}_Quiz{i}_{suffix}"
                quiz_ids.append(q_id)
                new_data.append({
                    'task_id': q_id,
                    'task_name': f"{sub_name} - Quiz {i} ({suffix})",
                    'estimated_duration_minutes': random.randint(30, 45),
                    'deadline': (datetime(2026, 4, 1) + timedelta(days=i*7 + iteration*2)).strftime('%Y-%m-%d %H:%M'),
                    'priority_level': 'Medium',
                    'cognitive_load': random.randint(2, 4),
                    'prerequisites': [quiz_ids[i-2]] if i > 1 else [] # Quiz 2 đợi Quiz 1
                })

            # --- 2. TẠO BÀI TẬP LỚN (BTL) ---
            btl1_id = f"{sub_id}_BTL1_{suffix}"
            new_data.append({
                'task_id': btl1_id,
                'task_name': f"{sub_name} - BTL 1 ({suffix})",
                'estimated_duration_minutes': random.randint(180, 360),
                'deadline': (datetime(2026, 5, 1) + timedelta(days=iteration)).strftime('%Y-%m-%d %H:%M'),
                'priority_level': 'High',
                'cognitive_load': random.randint(6, 8),
                'prerequisites': [quiz_ids[0]] # Xong Quiz 1 mới làm BTL 1
            })
            
            last_btl_id = btl1_id
            # Kiểm tra nếu môn này có 2 BTL
            if sub_id in subjects_with_2_btl:
                btl2_id = f"{sub_id}_BTL2_{suffix}"
                new_data.append({
                    'task_id': btl2_id,
                    'task_name': f"{sub_name} - BTL 2 ({suffix})",
                    'estimated_duration_minutes': random.randint(240, 480),
                    'deadline': (datetime(2026, 5, 20) + timedelta(days=iteration)).strftime('%Y-%m-%d %H:%M'),
                    'priority_level': 'High',
                    'cognitive_load': random.randint(8, 10),
                    'prerequisites': [btl1_id] # BTL 2 đợi BTL 1
                })
                last_btl_id = btl2_id

            # --- 3. BÀI GIỮA KỲ (GK) ---
            gk_id = f"{sub_id}_GK_{suffix}"
            new_data.append({
                'task_id': gk_id,
                'task_name': f"{sub_name} - Thi GK ({suffix})",
                'estimated_duration_minutes': 90,
                'deadline': (datetime(2026, 5, 10) + timedelta(days=iteration)).strftime('%Y-%m-%d %H:%M'),
                'priority_level': 'High',
                'cognitive_load': 7,
                'prerequisites': [quiz_ids[1]] # Xong Quiz 2 mới thi GK
            })

            # --- 4. BÀI CUỐI KỲ (CK) ---
            new_data.append({
                'task_id': f"{sub_id}_CK_{suffix}",
                'task_name': f"{sub_name} - Thi CK ({suffix})",
                'estimated_duration_minutes': 120,
                'deadline': (datetime(2026, 6, 15) + timedelta(days=iteration)).strftime('%Y-%m-%d %H:%M'),
                'priority_level': 'High',
                'cognitive_load': 9,
                'prerequisites': [gk_id, last_btl_id, quiz_ids[2]] # Phải xong hết mới thi CK
            })
        
        iteration += 1 # Tăng hậu tố nếu phải lặp lại danh sách môn lần nữa
        
    # Cắt bớt nếu lỡ dư dòng do vòng lặp for
    return pd.DataFrame(new_data[:target_rows])

# Thực thi
df_500 = generate_fake_dataset(df, 500)
print(f"Tổng số dòng đã tạo: {len(df_500)}")
df_500.to_csv('Data/df_500_tasks.csv', index=False)