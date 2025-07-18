from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
import enum

class UserRole(str, enum.Enum):
    admin = "admin"
    staff = "staff"
    customer = "customer"
    client = "client"  # Thêm client role để phù hợp với database

class User(Base):
    __tablename__ = "Users"  # Cập nhật tên table
    UserId = Column(Integer, primary_key=True, index=True)  # Cập nhật tên column
    Username = Column(String(50), unique=True, index=True, nullable=False)  # Cập nhật tên column
    PasswordHash = Column(String(255), nullable=False)  # Cập nhật tên column
    Role = Column(String(20), default="client")  # Cập nhật tên column và type
    entries = relationship("QueueEntry", back_populates="user")

class Queue(Base):
    __tablename__ = "Queues"  # Cập nhật tên table
    QueueId = Column(Integer, primary_key=True, index=True)  # Cập nhật tên column
    ServiceName = Column(String(100), nullable=False)  # Cập nhật tên column
    CreatedAt = Column(DateTime, default=datetime.utcnow)  # Cập nhật tên column
    entries = relationship("QueueEntry", back_populates="queue")

class QueueEntryStatus(str, enum.Enum):
    waiting = "waiting"
    serving = "serving"
    done = "done"
    skipped = "skipped"

class QueueEntry(Base):
    __tablename__ = "QueueEntries"  # Cập nhật tên table
    EntryId = Column(Integer, primary_key=True, index=True)  # Cập nhật tên column
    QueueId = Column(Integer, ForeignKey("Queues.QueueId"), default=1)  # Cập nhật tên column
    UserId = Column(Integer, ForeignKey("Users.UserId"), nullable=True)  # Cập nhật tên column
    Status = Column(String(20), default="waiting")  # Cập nhật tên column và type
    Position = Column(Integer)  # Thêm column Position
    CreatedAt = Column(DateTime, default=datetime.utcnow)  # Cập nhật tên column
    queue = relationship("Queue", back_populates="entries")
    user = relationship("User", back_populates="entries")
    history = relationship("ServeHistory", back_populates="queue_entry", uselist=False)

class ServeHistory(Base):
    __tablename__ = "ServeHistory"  # Cập nhật tên table
    HistoryId = Column(Integer, primary_key=True, index=True)  # Cập nhật tên column
    EntryId = Column(Integer, ForeignKey("QueueEntries.EntryId"))  # Cập nhật tên column
    ServedAt = Column(DateTime, default=datetime.utcnow)  # Cập nhật tên column
    queue_entry = relationship("QueueEntry", back_populates="history") 