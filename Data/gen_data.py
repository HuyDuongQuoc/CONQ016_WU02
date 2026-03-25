import pandas as pd
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker()
# 1. Đọc file với dấu phẩy
# 2. names=['ID', 'Subject', 'Credits'] để đặt tên cho các cột
# 3. header=None để báo cho Pandas biết dòng đầu tiên là dữ liệu, không phải tiêu đề
df = pd.read_csv('CS.csv', sep=',', names=['ID', 'Subject', 'Credits'], header=None)

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
df.to_csv('CS.csv', index=False)
fake_rows = []

for _ in range(500):
    # Chọn ngẫu nhiên một môn học từ danh sách gốc để lấy ID và Name
    idx = random.randint(0, len(df) - 1)
    base_row = df.iloc[idx]
    
    # Tạo dữ liệu fake cho các cột mới
    row = {
        'task_id': base_row['ID'],
        'task_name': f"{base_row['Subject']} - {fake.catch_phrase()}", # Thêm hậu tố cho đa dạng
        'estimated_duration_minutes': random.randint(30, 180), # Từ 30p đến 3 tiếng
        'deadline': fake.date_time_between(start_date='now', end_date='+30d'), # Deadline trong vòng 30 ngày tới
        'priority_level': random.choice(['Low', 'Medium', 'High']),
        'cognitive_load': round(random.uniform(1.0, 10.0), 1), # Điểm từ 1.0 đến 10.0
        'prerequisites': base_row['Prerequisite_Names']
    }
    fake_rows.append(row)

# Tạo DataFrame cuối cùng
df_fake = pd.DataFrame(fake_rows)

# --- Bước 3: Kiểm tra kết quả ---
print(df_fake.head(10))
df_fake.to_csv('df_fake', index=False)