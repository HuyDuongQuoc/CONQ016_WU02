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
df.to_csv('CS1.csv', index=False)
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

def generate_fake_dataset(source_df, total_rows=500):
    # 1. Chuyển đổi prerequisites sang tuple để có thể drop_duplicates nếu cần
    # (Nếu dữ liệu của ông đã sạch rồi thì có thể bỏ qua bước này)
    temp_df = source_df.copy()
    
    # 2. Chuyển DataFrame thành một "List of Lists" để random.choice hoạt động chuẩn xác
    # Chỉ lấy 3 cột quan trọng: id, name, prerequisites
    unique_tasks = temp_df[['ID', 'Subject', 'Prerequisite_Names']].values.tolist()
    
    new_data = []
    
    for i in range(total_rows):
        # random.choice giờ sẽ chọn một List [id, name, pre] từ unique_tasks
        base_task = random.choice(unique_tasks)
        base_id, base_name, base_pre = base_task
        
        # Tạo ID mới để tránh trùng Primary Key
        new_id = f"{base_id}_{i+1}"
        new_name = f"{base_name} (S{i+1})"
        
        # Các thông số ngẫu nhiên khác
        duration = random.randint(30, 240)
        # Tạo deadline rải rác trong tương lai
        deadline = datetime(2026, 4, 1) + timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
        priority = random.choice(['Low', 'Medium', 'High'])
        cog_load = random.randint(1, 10)
        
        new_data.append({
            'task_id': new_id,
            'task_name': new_name,
            'estimated_duration_minutes': duration,
            'deadline': deadline.strftime('%Y-%m-%d %H:%M'),
            'priority_level': priority,
            'cognitive_load': cog_load,
            'prerequisites': base_pre  # Giữ nguyên list gốc từ data của ông
        })
    
    return pd.DataFrame(new_data)

# Chạy lệnh này
df_500 = generate_fake_dataset(df, 500)

# Lưu lại kiểm tra
# df_500.to_csv("gen_data_500.csv", index=False)
print("Đã tạo xong 500 dòng!")

df_500.to_csv('df_500',index=False)