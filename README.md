# 🚀 Hướng Dẫn Dành Cho Thành Viên Đội Dự Án

Chào mừng mọi người đến với dự án **Smart Timetable & Task Optimizer**. Để đảm bảo code không bị xung đột và mọi người làm việc trơn tru, vui lòng đọc kỹ và làm theo quy trình dưới đây.

## 🛠️ Phần 1: Cài đặt ban đầu (Chỉ làm 1 lần duy nhất)

**Bước 1: Tải code về máy**
Mở terminal tại thư mục bạn muốn lưu dự án và chạy:
`git clone https://github.com/HuyDuongQuoc/CONQ016_WU02.git`
`cd CONQ016_WU02`

**Bước 2: Khởi tạo Môi trường ảo (Virtual Environment)**
Tuyệt đối không cài trực tiếp thư viện vào máy. Hãy tạo môi trường riêng cho dự án:
* **Windows:** `python -m venv venv`
* **Mac/Linux:** `python3 -m venv venv`

**Bước 3: Kích hoạt Môi trường ảo**
* **Windows:** `venv\Scripts\activate`
* **Mac/Linux:** `source venv/bin/activate`
*(Lưu ý: Bạn sẽ thấy chữ `(venv)` xuất hiện ở đầu dòng lệnh).*

**Bước 4: Cài đặt thư viện**
Chạy lệnh sau để máy tự động cài pandas, numpy, scikit-fuzzy, deap và streamlit:
`pip install -r requirements.txt`

---

## 🔄 Phần 2: Quy trình làm việc hàng ngày (Bắt buộc tuân thủ)

Mỗi khi bạn bắt đầu ngồi vào bàn code, hãy làm đúng theo 4 bước sau:

**1. Luôn cập nhật code mới nhất từ nhánh chính:**
`git checkout main`
`git pull origin main`

**2. Tạo nhánh làm việc riêng của bạn:**
Tuyệt đối KHÔNG code trực tiếp trên nhánh `main`. Hãy tạo nhánh mới theo tính năng bạn làm:
`git checkout -b feature/ten-tinh-nang`
*(Ví dụ: `git checkout -b feature/mock-data` hoặc `git checkout -b feature/giao-dien-dashboard`)*

**3. Lưu code cục bộ (Commit):**
Sau khi code xong một phần, hãy lưu lại với chú thích rõ ràng:
`git add .`
`git commit -m "Thêm hàm tính điểm Fuzzy mức cơ bản" `

**4. Đẩy lên GitHub và tạo Pull Request (PR):**
`git push origin feature/ten-tinh-nang`
Sau đó, lên trang web GitHub, bấm nút **"Compare & pull request"** và báo cho Trưởng nhóm vào review để gộp (merge) code vào nhánh `main`.

---

## ⚠️ 3 Nguyên Tắc Vàng
1. **Luôn nhớ kích hoạt `venv`** trước khi chạy code (`venv\Scripts\activate`).
2. **Kéo (Pull) code trước khi Đẩy (Push)** để tránh xung đột (Conflict).
3. Nếu cần cài thêm thư viện mới, hãy báo cho Trưởng nhóm để cập nhật vào file `requirements.txt`.
