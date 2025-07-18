from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import enum

class UserRole(str, enum.Enum):
    admin = "admin"
    staff = "staff"
    customer = "customer"
    client = "client"

class UserBase(BaseModel):
    Username: str
    Role: str

class UserCreate(BaseModel):
    Username: str
    password: str
    Role: Optional[str] = "client"

class UserOut(UserBase):
    UserId: int
    class Config:
        from_attributes = True

class QueueBase(BaseModel):
    ServiceName: str

class QueueCreate(QueueBase):
    pass

class QueueOut(QueueBase):
    QueueId: int
    CreatedAt: datetime
    class Config:
        from_attributes = True

class QueueEntryStatus(str, enum.Enum):
    waiting = "waiting"
    serving = "serving"
    done = "done"
    skipped = "skipped"

class QueueEntryBase(BaseModel):
    QueueId: int
    UserId: Optional[int]
    Status: str
    Position: Optional[int]

class QueueEntryCreate(BaseModel):
    QueueId: int
    UserId: Optional[int]

class QueueEntryOut(QueueEntryBase):
    EntryId: int
    CreatedAt: datetime
    class Config:
        from_attributes = True

class ServeHistoryBase(BaseModel):
    EntryId: int

class ServeHistoryCreate(ServeHistoryBase):
    pass

class ServeHistoryOut(ServeHistoryBase):
    HistoryId: int
    ServedAt: datetime
    class Config:
        from_attributes = True 