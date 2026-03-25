import pandas as pd

# 1. Đọc file với dấu phân cách là ';'
df = pd.read_csv('CS.csv', sep=';')

# 2. Ghi lại ra file mới với dấu phân cách mặc định là ','
df.to_csv('output_fixed.csv', index=False, encoding='utf-8')

print("Đã đổi dấu ';' sang ',' thành công!")