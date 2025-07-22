import models
import schemas
import database
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

# --- Cấu hình ---
SECRET_KEY = "queue-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()

origins = [
    "*"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # hoặc ['http://127.0.0.1:5500'] nếu muốn chặt hơn
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Database ---
models.Base.metadata.create_all(bind=database.engine)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Auth utils ---
def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- In-memory WebSocket manager ---
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
            await connection.send_json(message)

manager = ConnectionManager()

# --- API: Đăng ký, đăng nhập ---
@app.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.Username == user.Username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed = get_password_hash(user.password)
    db_user = models.User(Username=user.Username, PasswordHash=hashed, Role=user.Role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/login")
def login(form: schemas.UserCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.Username == form.Username).first()
    if not user or not verify_password(form.password, user.PasswordHash):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.Username, "role": user.Role})
    return {"access_token": access_token, "token_type": "bearer", "user": schemas.UserOut.from_orm(user)}

# --- API: Hàng đợi ---
@app.post("/queues", response_model=schemas.QueueOut)
def create_queue(queue: schemas.QueueCreate, db: Session = Depends(get_db)):
    db_queue = models.Queue(ServiceName=queue.ServiceName)
    db.add(db_queue)
    db.commit()
    db.refresh(db_queue)
    return db_queue

@app.get("/queues", response_model=List[schemas.QueueOut])
def get_queues(db: Session = Depends(get_db)):
    return db.query(models.Queue).all()

@app.get("/queue_entries", response_model=List[schemas.QueueEntryOut])
def get_queue_entries(db: Session = Depends(get_db)):
    return db.query(models.QueueEntry).all()

@app.post("/queue_entries", response_model=schemas.QueueEntryOut)
def add_queue_entry(entry: schemas.QueueEntryCreate, db: Session = Depends(get_db)):
    try:
        # Tính position cho entry mới
        last_position = db.query(models.QueueEntry).filter(
            models.QueueEntry.QueueId == entry.QueueId
        ).order_by(models.QueueEntry.Position.desc()).first()
        
        new_position = 1 if not last_position else last_position.Position + 1
        
        db_entry = models.QueueEntry(
            QueueId=entry.QueueId, 
            UserId=entry.UserId,
            Position=new_position,
            Status="waiting"
        )
        db.add(db_entry)
        db.commit()
        db.refresh(db_entry)
        # Broadcast cập nhật realtime
        send_queue_update(db)
        return db_entry
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error adding queue entry: {str(e)}")

@app.post("/queue_entries/{entry_id}/status")
def update_entry_status(entry_id: int, status: str, db: Session = Depends(get_db)):
    entry = db.query(models.QueueEntry).filter(models.QueueEntry.EntryId == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    entry.Status = status
    
    # Nếu status là "done", tạo record trong ServeHistory
    if status == "done":
        history = models.ServeHistory(EntryId=entry_id)
        db.add(history)
    
    db.commit()
    send_queue_update(db)
    return {"ok": True}

# --- API: Thống kê ---
@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    served_count = db.query(models.QueueEntry).filter(models.QueueEntry.Status == "done").count()
    waiting_count = db.query(models.QueueEntry).filter(models.QueueEntry.Status == "waiting").count()
    serving_count = db.query(models.QueueEntry).filter(models.QueueEntry.Status == "serving").count()
    avg_wait = 7  # Giả lập, có thể tính toán thực tế
    return {
        "servedCount": served_count, 
        "waitingCount": waiting_count,
        "servingCount": serving_count,
        "avgWaitTime": avg_wait
    }

# --- WebSocket realtime ---
@app.websocket("/ws/queue")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # giữ kết nối
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# --- Broadcast cập nhật hàng đợi ---
def send_queue_update(db: Session):
    # Lấy số đang phục vụ, danh sách chờ, số lượt phục vụ, thời gian chờ trung bình
    entries = db.query(models.QueueEntry).order_by(models.QueueEntry.Position).all()
    queue = [{"EntryId": e.EntryId, "Position": e.Position} for e in entries if e.Status == "waiting"]
    current_serving = next(({"EntryId": e.EntryId, "Position": e.Position} for e in entries if e.Status == "serving"), None)
    served_count = db.query(models.QueueEntry).filter(models.QueueEntry.Status == "done").count()
    waiting_count = db.query(models.QueueEntry).filter(models.QueueEntry.Status == "waiting").count()
    avg_wait = 7  # Giả lập
    
    # Chỉ broadcast nếu có active connections
    if manager.active_connections:
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(manager.broadcast({
                    "currentServing": current_serving,
                    "queue": queue,
                    "servedCount": served_count,
                    "waitingCount": waiting_count,
                    "avgWaitTime": avg_wait
                }))
        except RuntimeError:
            # Không có event loop, bỏ qua broadcast
            pass
