import hospital_models as models
import hospital_schemas as schemas
import database
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, Path, Body
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

class RoleUpdate(BaseModel):
    role: str

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

# CORS middleware
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database
models.Base.metadata.create_all(bind=database.engine)

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
        return {"username": username, "role": role}
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
        return db.query(models.User).filter(models.User.IsActive == True).all()
    elif token["role"] == "doctor":
        # Chỉ trả về danh sách bệnh nhân cho bác sĩ
        return db.query(models.User).filter(models.User.Role == "patient", models.User.IsActive == True).all()
    elif token["role"] == "patient":
        user = db.query(models.User).filter(models.User.Username == token["username"]).first()
        return [user] if user else []
    else:
        raise HTTPException(status_code=403, detail="Not authorized")

@app.get("/users/me", response_model=schemas.UserOut)
def get_current_user(db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    user = db.query(models.User).filter(models.User.Username == token["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

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
    query = db.query(models.Appointment)
    if department_id:
        query = query.filter(models.Appointment.DepartmentId == department_id)
    if status:
        query = query.filter(models.Appointment.Status == status)
    return query.order_by(models.Appointment.Position).all()

@app.post("/appointments", response_model=schemas.AppointmentOut)
def create_appointment(
    appointment: schemas.AppointmentCreate,
    db: Session = Depends(get_db)
):
    last_position = db.query(models.Appointment).filter(
        models.Appointment.DepartmentId == appointment.DepartmentId,
        models.Appointment.Status.in_(["waiting", "in_progress"])
    ).order_by(models.Appointment.Position.desc()).first()
    new_position = 1 if not last_position else last_position.Position + 1
    db_appointment = models.Appointment(
        **appointment.dict(),
        Position=new_position
    )
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    send_queue_update(db)
    return db_appointment

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

@app.get("/dashboard/stats")
def dashboard_stats(db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    from datetime import datetime
    today = datetime.utcnow().date()
    # Số bệnh nhân chờ xác nhận (waiting)
    waiting_patients = db.query(models.Appointment).filter(models.Appointment.Status == "waiting").count()
    # Số bệnh nhân đang khám (in_progress)
    in_progress_patients = db.query(models.Appointment).filter(models.Appointment.Status == "in_progress").count()
    # Số bệnh nhân đã hoàn thành trong ngày (completed)
    completed_today = db.query(models.Appointment).filter(
        models.Appointment.Status == "completed",
        models.Appointment.EndTime != None,
        cast(models.Appointment.EndTime, DATE) == today
    ).count()
    # Thời gian chờ trung bình (chỉ tính cho completed)
    avg_wait_time = db.execute(
        text("""
            SELECT AVG(DATEDIFF(MINUTE, ScheduledTime, StartTime))
            FROM Appointments
            WHERE Status = 'completed'
              AND StartTime IS NOT NULL
              AND ScheduledTime IS NOT NULL
              AND EndTime IS NOT NULL
              AND CAST(EndTime AS DATE) = :today
        """),
        {'today': today}
    ).scalar()
    if avg_wait_time:
        avg_wait_time = round(avg_wait_time)
    else:
        avg_wait_time = 0
    # Thống kê theo khoa
    departments = db.query(models.Department).all()
    department_stats = []
    for d in departments:
        waiting = db.query(models.Appointment).filter(models.Appointment.DepartmentId == d.DepartmentId, models.Appointment.Status == "waiting").count()
        in_progress = db.query(models.Appointment).filter(models.Appointment.DepartmentId == d.DepartmentId, models.Appointment.Status == "in_progress").count()
        completed = db.query(models.Appointment).filter(
            models.Appointment.DepartmentId == d.DepartmentId,
            models.Appointment.Status == "completed",
            models.Appointment.EndTime != None,
            cast(models.Appointment.EndTime, DATE) == today
        ).count()
        department_stats.append({
            "department_name": d.Name,
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
    if role in ["admin", "receptionist", "doctor", "patient"]:  # patient cũng xem toàn bộ
        departments = db.query(models.Department).all()
        for d in departments:
            waiting_queue = db.query(models.Appointment).filter(
                models.Appointment.DepartmentId == d.DepartmentId,
                models.Appointment.Status == "waiting"
            ).order_by(models.Appointment.Position).all()
            current_serving = db.query(models.Appointment).filter(
                models.Appointment.DepartmentId == d.DepartmentId,
                models.Appointment.Status == "in_progress"
            ).order_by(models.Appointment.Position).first()
            result.append({
                "department_id": d.DepartmentId,
                "department_name": d.Name,
                "waiting_queue": [
                    {
                        "patient_name": db.query(models.User).filter(models.User.UserId == w.PatientId).first().FullName,
                        "position": w.Position,
                        "scheduled_time": w.ScheduledTime.isoformat() if w.ScheduledTime else None
                    } for w in waiting_queue
                ],
                "current_serving": {
                    "patient_name": db.query(models.User).filter(models.User.UserId == current_serving.PatientId).first().FullName if current_serving else None,
                    "position": current_serving.Position if current_serving else None,
                    "scheduled_time": current_serving.ScheduledTime.isoformat() if current_serving and current_serving.ScheduledTime else None
                } if current_serving else None,
                "estimated_wait_time": len(waiting_queue) * 5
            })
        return result
    elif role == "nurse":
        user = db.query(models.User).filter(models.User.Username == username).first()
        doctor_departments = db.query(models.DoctorDepartment).filter(models.DoctorDepartment.DoctorId == user.UserId).all()
        for dd in doctor_departments:
            d = db.query(models.Department).filter(models.Department.DepartmentId == dd.DepartmentId).first()
            waiting_queue = db.query(models.Appointment).filter(
                models.Appointment.DepartmentId == d.DepartmentId,
                models.Appointment.Status == "waiting"
            ).order_by(models.Appointment.Position).all()
            current_serving = db.query(models.Appointment).filter(
                models.Appointment.DepartmentId == d.DepartmentId,
                models.Appointment.Status == "in_progress"
            ).order_by(models.Appointment.Position).first()
            result.append({
                "department_id": d.DepartmentId,
                "department_name": d.Name,
                "waiting_queue": [
                    {
                        "patient_name": db.query(models.User).filter(models.User.UserId == w.PatientId).first().FullName,
                        "position": w.Position
                    } for w in waiting_queue
                ],
                "current_serving": {
                    "patient_name": db.query(models.User).filter(models.User.UserId == current_serving.PatientId).first().FullName if current_serving else None,
                    "position": current_serving.Position if current_serving else None
                } if current_serving else None,
                "estimated_wait_time": len(waiting_queue) * 5
            })
    elif role == "patient":
        user = db.query(models.User).filter(models.User.Username == username).first()
        appointments = db.query(models.Appointment).filter(
            models.Appointment.PatientId == user.UserId,
            models.Appointment.Status.in_(["waiting", "in_progress"])
        ).all()
        for a in appointments:
            d = db.query(models.Department).filter(models.Department.DepartmentId == a.DepartmentId).first()
            waiting_queue = db.query(models.Appointment).filter(
                models.Appointment.DepartmentId == d.DepartmentId,
                models.Appointment.Status == "waiting"
            ).order_by(models.Appointment.Position).all()
            current_serving = db.query(models.Appointment).filter(
                models.Appointment.DepartmentId == d.DepartmentId,
                models.Appointment.Status == "in_progress"
            ).order_by(models.Appointment.Position).first()
            result.append({
                "department_id": d.DepartmentId,
                "department_name": d.Name,
                "waiting_queue": [
                    {
                        "patient_name": db.query(models.User).filter(models.User.UserId == w.PatientId).first().FullName,
                        "position": w.Position
                    } for w in waiting_queue
                ],
                "current_serving": {
                    "patient_name": db.query(models.User).filter(models.User.UserId == current_serving.PatientId).first().FullName if current_serving else None,
                    "position": current_serving.Position if current_serving else None
                } if current_serving else None,
                "my_position": a.Position,
                "my_status": a.Status,
                "estimated_wait_time": len(waiting_queue) * 5
            })
    return result

@app.post("/queue/start/{department_id}")
def start_queue(department_id: int = Path(...), db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    if token["role"] not in ["admin", "receptionist", "doctor", "nurse"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    appt = db.query(models.Appointment).filter(
        models.Appointment.DepartmentId == department_id,
        models.Appointment.Status == "waiting"
    ).order_by(models.Appointment.Position).first()
    if not appt:
        raise HTTPException(status_code=404, detail="No waiting appointment")
    appt.Status = "in_progress"
    db.commit()
    send_queue_update(db)
    return {"message": "Started serving"}

@app.post("/queue/complete/{department_id}")
def complete_queue(department_id: int = Path(...), db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    if token["role"] not in ["admin", "receptionist", "doctor", "nurse"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    appt = db.query(models.Appointment).filter(
        models.Appointment.DepartmentId == department_id,
        models.Appointment.Status == "in_progress"
    ).order_by(models.Appointment.Position).first()
    if not appt:
        raise HTTPException(status_code=404, detail="No in-progress appointment")
    appt.Status = "completed"
    from datetime import datetime
    appt.EndTime = datetime.utcnow()
    db.commit()
    # Sau khi hoàn thành, cập nhật lại Position cho các lịch hẹn còn lại
    remaining_appts = db.query(models.Appointment).filter(
        models.Appointment.DepartmentId == department_id,
        models.Appointment.Status.in_(["waiting", "in_progress"])
    ).order_by(models.Appointment.Position).all()
    for idx, a in enumerate(remaining_appts, start=1):
        a.Position = idx
    db.commit()
    send_queue_update(db)
    return {"message": "Completed appointment"}

class DoctorDepartmentIn(BaseModel):
    DoctorId: int
    DepartmentId: int
    IsPrimary: bool = False

@app.post("/doctor_departments")
def add_doctor_department(data: DoctorDepartmentIn, db: Session = Depends(get_db), token: dict = Depends(verify_token)):
    if token["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    entry = models.DoctorDepartment(
        DoctorId=data.DoctorId,
        DepartmentId=data.DepartmentId,
        IsPrimary=data.IsPrimary
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {"message": "Doctor assigned to department", "id": entry.Id}

@app.get("/")
def read_root():
    return {"message": "Hospital Queue Management System", "version": "1.0.0", "docs": "/docs"} 