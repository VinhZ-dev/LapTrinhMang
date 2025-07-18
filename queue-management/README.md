# Hệ Thống Quản Lý Hàng Đợi (Queue Management System)

Hệ thống quản lý hàng đợi thời gian thực được xây dựng với FastAPI, SQLAlchemy và SQL Server.

## Tính Năng

- ✅ **Quản lý hàng đợi thời gian thực** với WebSocket updates
- ✅ **Xác thực người dùng** với JWT tokens
- ✅ **Phân quyền theo vai trò** (admin, staff, customer)
- ✅ **Quản lý queue entries** (waiting, serving, done, skipped)
- ✅ **Theo dõi lịch sử phục vụ**
- ✅ **Dashboard admin** để quản lý hàng đợi
- ✅ **Giao diện staff** để phục vụ khách hàng
- ✅ **Kết nối SQL Server** hoàn chỉnh

## Yêu Cầu Hệ Thống

- Python 3.8+
- SQL Server 2019 hoặc mới hơn
- SQL Server Management Studio (SSMS)

## Cài Đặt và Chạy

### 1. Thiết Lập Database

#### Bước 1: Tạo Database trong SQL Server
Mở SQL Server Management Studio và chạy script sau:

```sql
-- Tạo database
CREATE DATABASE QueueManagement;
GO

-- Sử dụng database
USE QueueManagement;
GO

-- Tạo bảng Users
CREATE TABLE Users (
    UserId INT PRIMARY KEY IDENTITY,
    Username NVARCHAR(50),
    PasswordHash NVARCHAR(255),
    Role NVARCHAR(20)
);

-- Tạo bảng Queues
CREATE TABLE Queues (
    QueueId INT PRIMARY KEY IDENTITY,
    ServiceName NVARCHAR(100),
    CreatedAt DATETIME DEFAULT GETDATE()
);

-- Tạo bảng QueueEntries
CREATE TABLE QueueEntries (
    EntryId INT PRIMARY KEY IDENTITY,
    QueueId INT DEFAULT 1,
    UserId INT FOREIGN KEY REFERENCES Users(UserId),
    Status NVARCHAR(20),
    Position INT,
    CreatedAt DATETIME DEFAULT GETDATE()
);

-- Tạo bảng ServeHistory
CREATE TABLE ServeHistory (
    HistoryId INT PRIMARY KEY IDENTITY,
    EntryId INT FOREIGN KEY REFERENCES QueueEntries(EntryId),
    ServedAt DATETIME DEFAULT GETDATE()
);

-- Thêm dữ liệu mẫu
INSERT INTO Users (Username, PasswordHash, Role)
VALUES ('admin1', 'dummy-hash', 'admin');

-- Kiểm tra SQL Server version
SELECT @@VERSION AS 'SQL Server Version';
```

#### Bước 2: Cấu hình kết nối
Chỉnh sửa file `backend/database.py` nếu cần:

```python
SQLALCHEMY_DATABASE_URL = "mssql+pyodbc://@HP\\KANSQL/QueueManagement?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
```

### 2. Cài Đặt Backend

```bash
cd queue-management/backend

# Tạo virtual environment
python -m venv venv

# Kích hoạt virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt

# Khởi tạo database
python init_db.py

# Chạy server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Sử Dụng Frontend

Mở các file HTML trong trình duyệt:

- `frontend/index.html` - Giao diện khách hàng
- `frontend/staff.html` - Giao diện nhân viên
- `frontend/admin.html` - Giao diện quản trị

## API Endpoints

### Xác thực
- `POST /register` - Đăng ký người dùng mới
- `POST /login` - Đăng nhập

### Quản lý hàng đợi
- `POST /queues` - Tạo hàng đợi mới
- `GET /queues` - Lấy danh sách hàng đợi
- `POST /queue_entries` - Thêm entry vào hàng đợi
- `GET /queue_entries` - Lấy danh sách entries
- `POST /queue_entries/{entry_id}/status` - Cập nhật trạng thái entry

### Thống kê
- `GET /stats` - Lấy thống kê hàng đợi

### WebSocket
- `WS /ws/queue` - Cập nhật thời gian thực

## Tài Khoản Mặc Định

Sau khi chạy `init_db.py`, tài khoản admin sẽ được tạo:
- **Username**: admin1
- **Password**: admin123
- **Role**: admin

## Kiểm Tra Hệ Thống

Chạy script test để kiểm tra API:

```bash
python test_api.py
```

Kết quả mong đợi:
```
Queues API - Status: 200
Stats API - Status: 200
Queue Entries API - Status: 200
Add Queue Entry API - Status: 200
```

## Cấu Trúc Dự Án

```
queue-management/
├── backend/
│   ├── database.py          # Cấu hình database
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── main.py              # FastAPI application
│   ├── init_db.py           # Khởi tạo database
│   ├── test_api.py          # Test API
│   └── requirements.txt     # Python dependencies
└── frontend/
    ├── index.html           # Giao diện khách hàng
    ├── staff.html           # Giao diện nhân viên
    ├── admin.html           # Giao diện quản trị
    ├── app.js               # JavaScript frontend
    └── style.css            # CSS styling
```

## Tính Năng Đã Hoàn Thành

✅ **Backend API hoàn chỉnh**
- FastAPI với SQLAlchemy
- Kết nối SQL Server thành công
- WebSocket real-time updates
- JWT authentication
- CRUD operations cho queue

✅ **Database Schema**
- Users table với roles
- Queues table
- QueueEntries table với positions
- ServeHistory table

✅ **Frontend Integration**
- Kết nối API thực tế
- WebSocket real-time updates
- UI responsive
- Staff controls

✅ **Testing**
- API endpoints working
- Database operations successful
- Real-time updates functional

## Hướng Dẫn Sử Dụng

### Cho Khách Hàng
1. Mở `index.html`
2. Xem số hiện tại đang được phục vụ
3. Xem danh sách chờ và thời gian ước tính

### Cho Nhân Viên
1. Mở `staff.html`
2. Nhấn "Next" để gọi khách tiếp theo
3. Nhấn "Done" khi hoàn thành
4. Nhấn "Skip" để bỏ qua

### Cho Admin
1. Mở `admin.html`
2. Xem thống kê tổng quan
3. Theo dõi hiệu suất hệ thống

## Troubleshooting

### Lỗi kết nối SQL Server
- Kiểm tra SQL Server đang chạy
- Kiểm tra connection string trong `database.py`
- Đảm bảo Windows Authentication được bật

### Lỗi API 500
- Kiểm tra logs của server
- Đảm bảo database schema đúng
- Kiểm tra dependencies đã cài đầy đủ

### WebSocket không hoạt động
- Kiểm tra server đang chạy
- Kiểm tra CORS settings
- Kiểm tra firewall settings

## Phát Triển Thêm

Để mở rộng hệ thống, có thể thêm:

1. **Authentication UI** - Giao diện đăng nhập/đăng ký
2. **Multiple Queues** - Hỗ trợ nhiều hàng đợi
3. **User Management** - Quản lý người dùng
4. **Reports** - Báo cáo chi tiết
5. **Notifications** - Thông báo SMS/Email
6. **Mobile App** - Ứng dụng di động

## Liên Hệ

Hệ thống đã được test và hoạt động hoàn chỉnh với SQL Server. Mọi thắc mắc vui lòng liên hệ để được hỗ trợ. 