# Hospital Management System - Backend

Hệ thống quản lý bệnh viện với API backend sử dụng FastAPI và SQLite.

## 🚀 Cách chạy ứng dụng

### Phương pháp 1: Sử dụng script tự động (Khuyến nghị)

```bash
# Chạy script tự động
python run_app.py
```

Script này sẽ:
- Kiểm tra và cài đặt dependencies
- Khởi tạo database
- Tạo dữ liệu mẫu
- Khởi động server

### Phương pháp 2: Chạy thủ công

#### Bước 1: Cài đặt dependencies
```bash
pip install -r requirements.txt
```

#### Bước 2: Khởi tạo database
```bash
python init_db.py
```

#### Bước 3: Khởi động server
```bash
uvicorn hospital_api:app --host 0.0.0.0 --port 8000 --reload
```

## 📋 Thông tin đăng nhập mẫu

Sau khi chạy `init_db.py`, các tài khoản sau sẽ được tạo:

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Doctor | doctor | doctor123 |
| Receptionist | receptionist | receptionist123 |
| Patient | patient | patient123 |

## 🌐 URLs

- **Frontend**: http://127.0.0.1:5502/queue-management/frontend/hospital/login.html
- **Backend API**: http://127.0.0.1:8000
- **API Documentation**: http://127.0.0.1:8000/docs
- **Realtime API**: http://127.0.0.1:8000/docs

## 🗄️ Database

Ứng dụng sử dụng SQLite database được lưu trong file `data/hospital.db`.

### Cấu trúc database:
- **Users**: Thông tin người dùng (admin, doctor, receptionist, patient)
- **Departments**: Thông tin các khoa
- **Appointments**: Lịch hẹn khám bệnh
- **QueueEntries**: Hàng đợi khám bệnh
- **MedicalRecords**: Hồ sơ y tế
- **Notifications**: Thông báo

## 🔧 Troubleshooting

### Lỗi "Cannot connect to server"
- Đảm bảo server backend đang chạy trên port 8000
- Kiểm tra URL trong frontend có đúng không

### Lỗi database
- Xóa file `data/hospital.db` và chạy lại `init_db.py`
- Kiểm tra quyền ghi trong thư mục `data/`

### Lỗi dependencies
- Chạy `pip install -r requirements.txt`
- Hoặc sử dụng `python run_app.py` để tự động cài đặt

## 📁 Cấu trúc thư mục

```
backend/
├── data/                   # Database files
├── hospital_api.py         # Main API file
├── hospital_models.py      # Database models
├── hospital_schemas.py     # Pydantic schemas
├── database.py            # Database configuration
├── init_db.py             # Database initialization
├── run_app.py             # Auto-run script
├── requirements.txt       # Dependencies
└── README.md             # This file
```

## 🛠️ Development

### Thêm API endpoint mới:
1. Thêm route trong `hospital_api.py`
2. Thêm schema trong `hospital_schemas.py` (nếu cần)
3. Thêm model trong `hospital_models.py` (nếu cần)

### Thay đổi database:
1. Cập nhật models trong `hospital_models.py`
2. Xóa file `data/hospital.db`
3. Chạy lại `init_db.py`

## 📞 Support

Nếu gặp vấn đề, hãy kiểm tra:
1. Console logs của server
2. Browser developer tools
3. Database file có tồn tại không
4. Dependencies đã được cài đặt đầy đủ chưa 