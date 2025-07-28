import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import database
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, Path, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import asyncio
from sqlalchemy import func, and_, cast, DATE, text
from pydantic import BaseModel
import traceback
import hospital_models as models
import hospital_schemas as schemas

class RoleUpdate(BaseModel):
    role: str
    admin_password: str

# Configuration
SECRET_KEY = "hospital-secret-key-2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

app = FastAPI(
    title="Hospital Queue Management System",
    description="A comprehensive hospital queue management system with real-time updates",
    version="1.0.0"
)

# Sửa CORS cho phép mọi origin (hoặc đúng origin frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Hoặc chỉ ["http://127.0.0.1:5500"] nếu muốn an toàn hơn
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Database
try:
    # Kiểm tra kết nối database
    from database import test_connection
    if test_connection():
        print("✅ Connected to SQL Server database")
    else:
        print("❌ Failed to connect to database")
    
    # Không tạo bảng mới vì đã có trong SQL Server
    # models.Base.metadata.create_all(bind=database.engine)
    
    # Kiểm tra dữ liệu hiện có
    from database import SessionLocal
    db = SessionLocal()
    try:
        user_count = db.query(models.User).count()
        print(f"📊 Database has {user_count} users")
        
        # Hiển thị danh sách users hiện có
        users = db.query(models.User).all()
        print("👥 Available users:")
        for user in users:
            print(f"  - {user.Username} ({user.Role})")
            
    except Exception as e:
        print(f"⚠️ Could not read users: {e}")
    finally:
        db.close()
        
except Exception as e:
    print(f"❌ Database error: {e}")

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Authentication utilities
def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        # Lấy user_id từ DB
        from hospital_models import User
        from database import SessionLocal
        db = SessionLocal()
        user = db.query(User).filter(User.Username == username).first()
        db.close()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return {"username": username, "role": role, "user_id": user.UserId}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# WebSocket manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass
manager = ConnectionManager()

# Authentication endpoints
@app.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.Username == user.Username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed = get_password_hash(user.password)
    db_user = models.User(
        Username=user.Username,
        PasswordHash=hashed,
        Email=user.Email,
        Phone=user.Phone,
        FullName=user.FullName,
        DateOfBirth=user.DateOfBirth,
        Gender=user.Gender,
        Address=user.Address,
        Role=user.Role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/login", response_model=schemas.LoginResponse)
def login(login_data: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.Username == login_data.username).first()
    if not user or not verify_password(login_data.password, user.PasswordHash):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.Username, "role": user.Role})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": schemas.UserOut.from_orm(user)
    }

# Department endpoints
@app.get("/departments", response_model=List[schemas.DepartmentOut])
def get_departments(db: Session = Depends(get_db)):
    return db.query(models.Department).filter(models.Department.IsActive == True).all()

@app.post("/departments", response_model=schemas.DepartmentOut)
def create_department(
    department: schemas.DepartmentCreate,
    db: Session = Depends(get_db),
    token: dict = Depends(verify_token)
):
    if token["role"] not in ["admin", "receptionist"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    db_department = models.Department(**department.dict())
    db.add(db_department)
    db.commit()
    db.refresh(db_department)
    return db_department

# User endpoints
@app.get("/users", response_model=List[schemas.UserOut])
def get_users(
    db: Session = Depends(get_db),
    token: dict = Depends(verify_token)
):
    if token["role"] in ["admin", "receptionist"]:
        users = db.query(models.User).filter(models.User.IsActive == True).all()
        result = []
        for u in users:
            user_dict = u.__dict__.copy()
            if u.Role == "doctor":
                doc_dept = db.query(models.DoctorDepartment).filter(models.DoctorDepartment.DoctorId == u.UserId).first()
                if doc_dept:
                    dept = db.query(models.Department).filter(models.Department.DepartmentId == doc_dept.DepartmentId).first()
                    user_dict["DepartmentName"] = dept.Name if dept else None
                else:
                    user_dict["DepartmentName"] = None
            else:
                user_dict["DepartmentName"] = None
            result.append(schemas.UserOut(**user_dict))
        return result
    elif token["role"] == "doctor":
        # Chỉ trả về danh sách bệnh nhân cho bác sĩ
        return db.query(models.User).filter(models.User.Role == "patient", models.User.IsActive == True).all()
    elif token["role"] == "patient":
        user = db.query(models.User).filter(models.User.Username == token["username"]).first()
        if user:
            user_dict = user.__dict__.copy()
            if user.Role == "doctor":
                doc_dept = db.query(models.DoctorDepartment).filter(models.DoctorDepartment.DoctorId == user.UserId).first()
                if doc_dept:
                    dept = db.query(models.Department).filter(models.Department.DepartmentId == doc_dept.DepartmentId).first()
                    user_dict["DepartmentName"] = dept.Name if dept else None
                else:
                    user_dict["DepartmentName"] = None
            else:
                user_dict["DepartmentName"] = None
            return [schemas.UserOut(**user_dict)]
        return []
    else:
        raise HTTPException(status_code=403, detail="Not authorized")

@app.get("/users/me", response_model=schemas.UserOut)
def get_current_user(db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    user = db.query(models.User).filter(models.User.Username == token["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_dict = user.__dict__.copy()
    if user.Role == "doctor":
        doc_dept = db.query(models.DoctorDepartment).filter(models.DoctorDepartment.DoctorId == user.UserId).first()
        if doc_dept:
            dept = db.query(models.Department).filter(models.Department.DepartmentId == doc_dept.DepartmentId).first()
            user_dict["DepartmentName"] = dept.Name if dept else None
        else:
            user_dict["DepartmentName"] = None
    else:
        user_dict["DepartmentName"] = None
    return schemas.UserOut(**user_dict)

@app.put("/users/me", response_model=schemas.UserOut)
def update_current_user(
    user_update: schemas.UserUpdate = Body(...),
    db: Session = Depends(get_db),
    token: dict = Depends(verify_token)
):
    user = db.query(models.User).filter(models.User.Username == token["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Cập nhật các trường cho phép
    for field in ["FullName", "Email", "Phone", "DateOfBirth", "Gender", "Address"]:
        if hasattr(user_update, field) and getattr(user_update, field) is not None:
            setattr(user, field, getattr(user_update, field))
    db.commit()
    db.refresh(user)
    return user

@app.put("/users/{user_id}/role")
def update_user_role(user_id: int, data: RoleUpdate, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    if token["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    # Xác thực mật khẩu admin
    admin = db.query(models.User).filter(models.User.Username == token["username"]).first()
    if not admin or not verify_password(data.admin_password, admin.PasswordHash):
        raise HTTPException(status_code=401, detail="Mật khẩu admin không đúng")
    user = db.query(models.User).filter(models.User.UserId == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.Role = data.role
    db.commit()
    db.refresh(user)
    return {"message": "Role updated"}

@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    if token["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    user = db.query(models.User).filter(models.User.UserId == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Xóa tất cả lịch hẹn liên quan trước
    db.query(models.Appointment).filter(models.Appointment.PatientId == user_id).delete()
    db.query(models.Appointment).filter(models.Appointment.DoctorId == user_id).delete()
    # Xóa user
    db.delete(user)
    db.commit()
    return {"message": "User deleted"}

@app.get("/users/doctors", response_model=List[schemas.UserOut])
def get_doctors(db: Session = Depends(get_db)):
    return db.query(models.User).filter(
        models.User.Role == "doctor",
        models.User.IsActive == True
    ).all()

# Appointment endpoints
@app.get("/appointments", response_model=List[schemas.AppointmentOut])
def get_appointments(
    department_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    token: dict = Depends(verify_token)
):
    # Chỉ cho phép admin, doctor, receptionist xem tất cả lịch hẹn
    if token["role"] in ["admin", "doctor", "receptionist"]:
        query = db.query(models.Appointment)
        if department_id:
            query = query.filter(models.Appointment.DepartmentId == department_id)
        if status:
            query = query.filter(models.Appointment.Status == status)
        return query.order_by(models.Appointment.Position).all()
    elif token["role"] == "patient":
        user = db.query(models.User).filter(models.User.Username == token["username"]).first()
        if not user:
            raise HTTPException(status_code=403, detail="Not authorized")
        query = db.query(models.Appointment).filter(models.Appointment.PatientId == user.UserId)
        if department_id:
            query = query.filter(models.Appointment.DepartmentId == department_id)
        if status:
            query = query.filter(models.Appointment.Status == status)
        return query.order_by(models.Appointment.Position).all()
    else:
        raise HTTPException(status_code=403, detail="Not authorized")

@app.post("/appointments", response_model=schemas.AppointmentOut)
def create_appointment(
    appointment: schemas.AppointmentCreate,
    db: Session = Depends(get_db),
    token: dict = Depends(verify_token)
):
    # Cho phép cả bệnh nhân tự tạo lịch hẹn
    if token["role"] == "patient":
        user = db.query(models.User).filter(models.User.Username == token["username"]).first()
        if not user:
            raise HTTPException(status_code=403, detail="Not authorized")
        appointment.PatientId = user.UserId
    try:
        last_position = db.query(models.Appointment).filter(
            models.Appointment.DepartmentId == appointment.DepartmentId,
            models.Appointment.Status.in_(["waiting", "in_progress"])
        ).order_by(models.Appointment.Position.desc()).first()
        new_position = 1 if not last_position else last_position.Position + 1
        data = appointment.dict()
        data.pop("Status", None)  # Xóa Status nếu có
        db_appointment = models.Appointment(
            **data,
            Status="waiting",
            Position=new_position
        )
        db.add(db_appointment)
        db.commit()
        db.refresh(db_appointment)
        send_queue_update(db)
        return db_appointment
    except Exception as e:
        print('Error creating appointment:', e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/appointments/{appointment_id}/cancel")
def cancel_appointment(appointment_id: int = Path(...), db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    appt = db.query(models.Appointment).filter(models.Appointment.AppointmentId == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appt.Status in ["completed", "cancelled"]:
        raise HTTPException(status_code=400, detail="Appointment already completed or cancelled")
    appt.Status = "cancelled"
    db.commit()
    send_queue_update(db)
    return {"message": "Appointment cancelled"}

@app.delete("/appointments/{appointment_id}")
def delete_appointment(appointment_id: int = Path(...), db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    appt = db.query(models.Appointment).filter(models.Appointment.AppointmentId == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appt.Status not in ["completed", "cancelled"]:
        raise HTTPException(status_code=400, detail="Chỉ được xóa lịch hẹn đã hoàn thành hoặc đã hủy")
    db.delete(appt)
    db.commit()
    send_queue_update(db)
    return {"message": "Appointment deleted"}

@app.post("/appointments/{appointment_id}/confirm")
def confirm_appointment(appointment_id: int, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    # Lấy thông tin lịch hẹn
    appt = db.query(models.Appointment).filter(models.Appointment.AppointmentId == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appt.Status != "waiting":
        raise HTTPException(status_code=400, detail="Chỉ xác nhận lịch hẹn ở trạng thái 'waiting'")
    # Tạo bản ghi mới trong QueueEntries (QueueId = DepartmentId)
    queue = db.query(models.Queue).filter(models.Queue.QueueId == appt.DepartmentId).first()
    if not queue:
        queue = models.Queue(QueueId=appt.DepartmentId, ServiceName=f"Department {appt.DepartmentId}")
        db.add(queue)
        db.commit()
        db.refresh(queue)
    # Thêm bệnh nhân vào vị trí đầu tiên của hàng đợi
    entry = models.QueueEntry(
        QueueId=queue.QueueId,
        UserId=appt.PatientId,
        Position=1,
        Status="waiting"
    )
    db.add(entry)
    
    # Cập nhật trạng thái lịch hẹn
    appt.Status = "confirmed"
    db.commit()
    db.refresh(entry)

    # Sau khi thêm vào hàng đợi, cập nhật lại Position cho các QueueEntry còn lại (Status='waiting')
    # Đẩy tất cả bệnh nhân khác xuống 1 vị trí
    waiting_entries = db.query(models.QueueEntry).filter(
        models.QueueEntry.QueueId == queue.QueueId,
        models.QueueEntry.Status == "waiting",
        models.QueueEntry.EntryId != entry.EntryId  # Không bao gồm entry vừa thêm
    ).order_by(models.QueueEntry.Position).all()
    
    for idx, e in enumerate(waiting_entries, start=2):  # Bắt đầu từ vị trí 2
        e.Position = idx
    db.commit()
    return {"message": "Appointment confirmed and added to queue", "queue_entry_id": entry.EntryId}

@app.get("/appointments/{appointment_id}", response_model=schemas.AppointmentOut)
def get_appointment_detail(appointment_id: int, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    appt = db.query(models.Appointment).filter(models.Appointment.AppointmentId == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if token["role"] == "patient":
        user = db.query(models.User).filter(models.User.Username == token["username"]).first()
        if not user or appt.PatientId != user.UserId:
            raise HTTPException(status_code=403, detail="Not authorized")
    # Lấy thông tin bệnh nhân và bác sĩ
    patient = db.query(models.User).filter(models.User.UserId == appt.PatientId).first()
    doctor = db.query(models.User).filter(models.User.UserId == appt.DoctorId).first() if appt.DoctorId else None
    appt_out = schemas.AppointmentOut.from_orm(appt)
    appt_out.Patient = schemas.UserOut.from_orm(patient) if patient else None
    appt_out.Doctor = schemas.UserOut.from_orm(doctor) if doctor else None
    return appt_out

@app.put("/appointments/{appointment_id}", response_model=schemas.AppointmentOut)
def update_appointment(appointment_id: int, update: schemas.AppointmentCreate, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    if token["role"] not in ["admin", "doctor", "receptionist"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    appt = db.query(models.Appointment).filter(models.Appointment.AppointmentId == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    for field, value in update.dict(exclude_unset=True).items():
        if field != "PatientId":
            setattr(appt, field, value)
    db.commit()
    db.refresh(appt)
    return appt

# WebSocket endpoint
@app.websocket("/ws/queue")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

def send_queue_update(db: Session):
    if manager.active_connections:
        try:
            # Chỉ gửi thông báo đơn giản cho demo
            asyncio.create_task(manager.broadcast({"type": "queue_update"}))
        except:
            pass

# Thêm hàm gửi notification (đặt ở đầu file, sau import)
def send_notification(db, user_id, title, message, type_="info"):
    from hospital_models import Notification
    notification = Notification(
        UserId=user_id,
        Title=title,
        Message=message,
        Type=type_,
        IsRead=False
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification

@app.get("/dashboard/stats")
def dashboard_stats(db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    # Thống kê dựa trên QueueEntries
    waiting_patients = db.query(models.QueueEntry).filter(models.QueueEntry.Status == "waiting").count()
    in_progress_patients = db.query(models.QueueEntry).filter(models.QueueEntry.Status == "serving").count()
    completed_today = db.query(models.ServeHistory).count()  # Đơn giản hóa, có thể lọc theo ngày nếu cần
    avg_wait_time = 7  # Có thể tính toán thực tế nếu có thời gian vào/ra
    # Thống kê theo khoa
    queues = db.query(models.Queue).all()
    department_stats = []
    for q in queues:
        department = db.query(models.Department).filter(models.Department.DepartmentId == q.QueueId).first()
        department_name = department.Name if department else f"Department {q.QueueId}"
        waiting = db.query(models.QueueEntry).filter(models.QueueEntry.QueueId == q.QueueId, models.QueueEntry.Status == "waiting").count()
        in_progress = db.query(models.QueueEntry).filter(models.QueueEntry.QueueId == q.QueueId, models.QueueEntry.Status == "serving").count()
        completed = db.query(models.QueueEntry).filter(models.QueueEntry.QueueId == q.QueueId, models.QueueEntry.Status == "done").count()
        department_stats.append({
            "department_name": department_name,
            "waiting": waiting,
            "in_progress": in_progress,
            "completed": completed
        })
    return {
        "waiting_patients": waiting_patients,
        "in_progress_patients": in_progress_patients,
        "completed_today": completed_today,
        "avg_wait_time": avg_wait_time,
        "department_stats": department_stats
    }

@app.get("/queue/status")
def queue_status(db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    role = token["role"]
    username = token["username"]
    result = []
    # Lấy danh sách tất cả Queue (theo khoa)
    queues = db.query(models.Queue).all()
    for q in queues:
        # Lấy danh sách hàng đợi thực tế từ QueueEntries
        waiting_entries = db.query(models.QueueEntry).filter(
            models.QueueEntry.QueueId == q.QueueId,
            models.QueueEntry.Status == "waiting"
        ).order_by(models.QueueEntry.Position).all()
        serving_entry = db.query(models.QueueEntry).filter(
            models.QueueEntry.QueueId == q.QueueId,
            models.QueueEntry.Status == "serving"
        ).order_by(models.QueueEntry.Position).first()
        # Lấy tên khoa
        department = db.query(models.Department).filter(models.Department.DepartmentId == q.QueueId).first()
        department_name = department.Name if department else f"Department {q.QueueId}"
        # Lấy thông tin bệnh nhân
        waiting_queue = []
        for w in waiting_entries:
            user = db.query(models.User).filter(models.User.UserId == w.UserId).first()
            waiting_queue.append({
                "patient_name": user.FullName if user else f"User {w.UserId}",
                "position": w.Position
            })
        current_serving = None
        if serving_entry:
            user = db.query(models.User).filter(models.User.UserId == serving_entry.UserId).first()
            current_serving = {
                "patient_name": user.FullName if user else f"User {serving_entry.UserId}",
                "position": serving_entry.Position
            }
        result.append({
            "department_id": q.QueueId,
            "department_name": department_name,
            "waiting_queue": waiting_queue,
            "current_serving": current_serving,
            "estimated_wait_time": len(waiting_queue) * 5
        })
    return result

@app.post("/queue/start/{queue_id}")
def start_queue(queue_id: int = Path(...), db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    if token["role"] not in ["admin", "receptionist", "doctor", "nurse"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    # Lấy entry đầu tiên đang chờ (Position = 1)
    entry = db.query(models.QueueEntry).filter(
        models.QueueEntry.QueueId == queue_id,
        models.QueueEntry.Status == "waiting"
    ).order_by(models.QueueEntry.Position).first()
    if not entry:
        raise HTTPException(status_code=404, detail="No waiting entry")
    entry.Status = "serving"
    db.commit()
    # Gửi thông báo cho bệnh nhân này: "Bắt đầu vào khám"
    if entry.UserId:
        send_notification(db, entry.UserId, "Bắt đầu khám", "Bạn đã được gọi vào khám. Vui lòng di chuyển vào phòng khám.", "info")
    # Gửi thông báo cho người tiếp theo (nếu có): "Sắp tới lượt khám"
    next_entry = db.query(models.QueueEntry).filter(
        models.QueueEntry.QueueId == queue_id,
        models.QueueEntry.Status == "waiting",
        models.QueueEntry.Position == 2
    ).first()
    if next_entry and next_entry.UserId:
        send_notification(db, next_entry.UserId, "Sắp tới lượt khám", "Bạn là người tiếp theo, hãy chuẩn bị vào khám.", "info")
    send_queue_update(db)
    return {"message": "Started serving"}

@app.post("/queue/complete/{queue_id}")
def complete_queue(queue_id: int = Path(...), db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    if token["role"] not in ["admin", "receptionist", "doctor", "nurse"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    # Lấy entry đang phục vụ
    entry = db.query(models.QueueEntry).filter(
        models.QueueEntry.QueueId == queue_id,
        models.QueueEntry.Status == "serving"
    ).order_by(models.QueueEntry.Position).first()
    if not entry:
        raise HTTPException(status_code=404, detail="No serving entry")
    entry.Status = "done"
    from datetime import datetime
    # Lưu vào ServeHistory nếu chưa có
    existing_history = db.query(models.ServeHistory).filter(models.ServeHistory.EntryId == entry.EntryId).first()
    if not existing_history:
        history = models.ServeHistory(EntryId=entry.EntryId, ServedAt=datetime.utcnow())
        db.add(history)
    db.commit()
    # Gửi thông báo cho bệnh nhân này: "Hoàn thành khám"
    if entry.UserId:
        send_notification(db, entry.UserId, "Hoàn thành khám", "Bạn đã hoàn thành lượt khám. Cảm ơn bạn!", "success")
    # Sau khi hoàn thành, cập nhật lại Position cho các QueueEntry còn lại (Status='waiting')
    # Đánh lại số thứ tự từ 1 cho các bệnh nhân còn chờ
    waiting_entries = db.query(models.QueueEntry).filter(
        models.QueueEntry.QueueId == queue_id,
        models.QueueEntry.Status == "waiting"
    ).order_by(models.QueueEntry.Position).all()
    for idx, e in enumerate(waiting_entries, start=1):
        e.Position = idx
    db.commit()
    # Gửi thông báo cho người tiếp theo (nếu có): "Sắp tới lượt khám"
    if waiting_entries:
        first_waiting = waiting_entries[0]
        if first_waiting.UserId:
            send_notification(db, first_waiting.UserId, "Sắp tới lượt khám", "Bạn là người tiếp theo, hãy chuẩn bị vào khám.", "info")
    send_queue_update(db)
    return {"message": "Completed entry"}

class DoctorDepartmentIn(BaseModel):
    DoctorId: int
    DepartmentId: int
    IsPrimary: bool = False

@app.post("/doctor_departments", response_model=schemas.DoctorDepartmentOut)
def add_doctor_department(data: DoctorDepartmentIn, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    # Chỉ cho phép admin hoặc chính bác sĩ đó chỉnh sửa
    if token["role"] != "admin" and token["user_id"] != data.DoctorId:
        raise HTTPException(status_code=403, detail="Not authorized")
    # Xóa tất cả các khoa cũ của bác sĩ này
    db.query(models.DoctorDepartment).filter(models.DoctorDepartment.DoctorId == data.DoctorId).delete()
    db.commit()
    # Thêm khoa mới
    doctor_dept = models.DoctorDepartment(
        DoctorId=data.DoctorId,
        DepartmentId=data.DepartmentId,
        IsPrimary=True
    )
    db.add(doctor_dept)
    db.commit()
    db.refresh(doctor_dept)
    # Lấy thông tin khoa
    dept = db.query(models.Department).filter(models.Department.DepartmentId == doctor_dept.DepartmentId).first()
    out = schemas.DoctorDepartmentOut.from_orm(doctor_dept)
    if dept:
        out.Department = schemas.DepartmentOut.from_orm(dept)
    return out

@app.get("/doctor_departments", response_model=List[schemas.DoctorDepartmentOut])
def get_doctor_departments(doctor_id: Optional[int] = Query(None), db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    try:
        if doctor_id is None:
            user = db.query(models.User).filter(models.User.Username == token["username"]).first()
            if not user or user.Role != "doctor":
                raise HTTPException(status_code=403, detail="Not authorized")
            doctor_id = user.UserId
        # Lấy duy nhất 1 bản ghi
        dd = db.query(models.DoctorDepartment).filter(models.DoctorDepartment.DoctorId == doctor_id).first()
        result = []
        if dd:
            dept = db.query(models.Department).filter(models.Department.DepartmentId == dd.DepartmentId).first()
            result.append({
                "Id": dd.Id,
                "DoctorId": dd.DoctorId,
                "DepartmentId": dd.DepartmentId,
                "IsPrimary": dd.IsPrimary,
                "CreatedAt": dd.CreatedAt,
                "Department": {
                    "DepartmentId": dept.DepartmentId if dept else None,
                    "Name": dept.Name if dept else None,
                    "Type": dept.Type if dept else None,
                    "Description": dept.Description if dept else None,
                    "Location": dept.Location if dept else None,
                    "Floor": dept.Floor if dept else None,
                    "RoomNumber": dept.RoomNumber if dept else None,
                    "IsActive": dept.IsActive if dept else None,
                    "CreatedAt": dept.CreatedAt if dept else None,
                    "UpdatedAt": dept.UpdatedAt if dept else None
                } if dept else None
            })
        return result
    except Exception as e:
        import traceback
        print(f"Error in /doctor_departments: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/notifications", response_model=List[schemas.NotificationOut])
def get_notifications(db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    # Chỉ cho phép bệnh nhân lấy thông báo của mình
    user = db.query(models.User).filter(models.User.Username == token["username"]).first()
    if not user or user.Role != "patient":
        raise HTTPException(status_code=403, detail="Not authorized")
    notifications = db.query(models.Notification).filter(models.Notification.UserId == user.UserId).order_by(models.Notification.CreatedAt.desc()).all()
    return notifications

@app.get("/")
def read_root():
    return {"message": "Hospital Queue Management System", "version": "1.0.0", "docs": "/docs"} 