import hospital_models as models
import hospital_schemas as schemas
import database
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import asyncio
from sqlalchemy import func, and_

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
    if token["role"] not in ["admin", "receptionist"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(models.User).filter(models.User.IsActive == True).all()

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
    # Tổng số bệnh nhân đang chờ
    waiting_patients = db.query(models.Appointment).filter(models.Appointment.Status == "waiting").count()
    # Tổng số bệnh nhân đang khám
    in_progress_patients = db.query(models.Appointment).filter(models.Appointment.Status == "in_progress").count()
    # Tổng số lịch hẹn hoàn thành trong ngày
    today = datetime.utcnow().date()
    completed_today = db.query(models.Appointment).filter(
        models.Appointment.Status == "completed",
        func.date(models.Appointment.EndTime) == today
    ).count()
    # Thời gian chờ trung bình (phút) của các lịch đã hoàn thành hôm nay
    avg_wait_time = db.query(func.avg(func.strftime('%s', models.Appointment.StartTime) - func.strftime('%s', models.Appointment.ScheduledTime))).filter(
        models.Appointment.Status == "completed",
        models.Appointment.StartTime != None,
        models.Appointment.ScheduledTime != None,
        func.date(models.Appointment.EndTime) == today
    ).scalar()
    if avg_wait_time:
        avg_wait_time = round(avg_wait_time / 60)
    else:
        avg_wait_time = 0
    # Thống kê theo khoa
    departments = db.query(models.Department).all()
    department_stats = []
    for d in departments:
        waiting = db.query(models.Appointment).filter(models.Appointment.DepartmentId == d.DepartmentId, models.Appointment.Status == "waiting").count()
        in_progress = db.query(models.Appointment).filter(models.Appointment.DepartmentId == d.DepartmentId, models.Appointment.Status == "in_progress").count()
        department_stats.append({
            "department_name": d.Name,
            "waiting": waiting,
            "in_progress": in_progress
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
    if role in ["admin", "receptionist"]:
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
                        "position": w.Position
                    } for w in waiting_queue
                ],
                "current_serving": {
                    "patient_name": db.query(models.User).filter(models.User.UserId == current_serving.PatientId).first().FullName if current_serving else None,
                    "position": current_serving.Position if current_serving else None
                } if current_serving else None,
                "estimated_wait_time": len(waiting_queue) * 5
            })
    elif role in ["doctor", "nurse"]:
        # Lấy khoa mà doctor/nurse phụ trách (giả sử có bảng DoctorDepartment)
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
        # Lấy tất cả các lịch hẹn của bệnh nhân này còn trong hàng đợi
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

@app.get("/")
def read_root():
    return {"message": "Hospital Queue Management System", "version": "1.0.0", "docs": "/docs"} 