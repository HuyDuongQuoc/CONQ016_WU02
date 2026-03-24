import pandas as pd
from faker import Faker
import random
from datetime import datetime, timedelta

# Khởi tạo Faker
fake = Faker()

# Danh sách tên task mẫu để trộn
task_templates = [
    "Computer Architecture Lab", "Philosophy Reading", "Calculus I",
    "Fundametal Programming", "Data Structure and Algorithm", "Database",
    "Introduction to Artificial Intelligence", "Mobile App Development", "Physics Experiment",
    "Digital System"
]

def generate_task_data(num_records=500):
    data = []
    
    for i in range(1, num_records + 1):
        # 1. task_id (Primary Key)
        task_id = f"TASK_{i:04d}"
        
        # 2. task_name
        name = f"{random.choice(task_templates)} {random.randint(1, 5)}"
        
        # 3. estimated_duration_minutes (ví dụ từ 30p đến 240p)
        duration = random.choice([30, 45, 60, 90, 120, 150, 180, 240])
        
        # 4. deadline (Trong vòng 30 ngày tới)
        deadline = fake.date_time_between(start_date='now', end_date='+30d')
        
        # 5. priority_level
        priority = random.choice(['Low', 'Medium', 'High'])
        
        # 6. cognitive_load (Thang điểm 1-10)
        cognitive_load = round(random.uniform(1.0, 10.0), 1)
        
        # 7. prerequisites (Danh sách các ID đã tạo trước đó)
        # Để tránh vòng lặp vô tận, task sau chỉ phụ thuộc task trước
        prereqs = []
        if i > 1 and random.random() < 0.3:  # 30% khả năng có tiền đề
            num_prereqs = random.randint(1, min(3, i-1))
            possible_ids = [f"TASK_{j:04d}" for j in range(1, i)]
            prereqs = random.sample(possible_ids, num_prereqs)

        data.append({
            "task_id": task_id,
            "task_name": name,
            "estimated_duration_minutes": duration,
            "deadline": deadline.strftime('%Y-%m-%d %H:%M:%S'),
            "priority_level": priority,
            "cognitive_load": cognitive_load,
            "prerequisites": prereqs  # Lưu dạng list
        })
    
    return data

# Thực hiện sinh dữ liệu
tasks = generate_task_data(500)

# Chuyển sang DataFrame
df = pd.DataFrame(tasks)

# Lưu file CSV (Lưu ý: prerequisites sẽ được lưu dưới dạng chuỗi đại diện cho list)
df.to_csv("tasks_data.csv", index=False, encoding="utf-8-sig")

print("Đã sinh xong 500 task vào file tasks_data.csv!")
print(df.head()) # Hiển thị 5 dòng đầu để kiểm tra