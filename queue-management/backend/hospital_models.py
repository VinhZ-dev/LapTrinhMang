from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Enum, Unicode, UnicodeText
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
import enum

class User(Base):
    __tablename__ = "Users"
    UserId = Column(Integer, primary_key=True, index=True)
    Username = Column(Unicode(50), unique=True, index=True, nullable=False)
    PasswordHash = Column(String(255), nullable=False)
    Role = Column(Unicode(20), nullable=False)
    Email = Column(Unicode(100))
    Phone = Column(String(20))
    FullName = Column(Unicode(100), nullable=False)
    DateOfBirth = Column(DateTime)
    Gender = Column(Unicode(10))
    Address = Column(UnicodeText)
    IsActive = Column(Boolean, default=True)
    CreatedAt = Column(DateTime, default=datetime.utcnow)
    UpdatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Relationships
    doctor_departments = relationship("DoctorDepartment", back_populates="doctor")
    appointments = relationship("Appointment", back_populates="patient", foreign_keys="Appointment.PatientId")
    doctor_appointments = relationship("Appointment", back_populates="doctor", foreign_keys="Appointment.DoctorId")

class Department(Base):
    __tablename__ = "Departments"
    DepartmentId = Column(Integer, primary_key=True, index=True)
    Name = Column(Unicode(100), nullable=False)
    Type = Column(Unicode(50), nullable=False)  # Tăng lên 50 ký tự
    Description = Column(UnicodeText)
    Location = Column(Unicode(100))
    Floor = Column(Unicode(10))
    RoomNumber = Column(Unicode(20))
    IsActive = Column(Boolean, default=True)
    CreatedAt = Column(DateTime, default=datetime.utcnow)
    UpdatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Relationships
    doctor_departments = relationship("DoctorDepartment", back_populates="department")
    appointments = relationship("Appointment", back_populates="department")

class DoctorDepartment(Base):
    __tablename__ = "DoctorDepartments"
    Id = Column(Integer, primary_key=True, index=True)
    DoctorId = Column(Integer, ForeignKey("Users.UserId"))
    DepartmentId = Column(Integer, ForeignKey("Departments.DepartmentId"))
    IsPrimary = Column(Boolean, default=False)
    CreatedAt = Column(DateTime, default=datetime.utcnow)
    # Relationships
    doctor = relationship("User", back_populates="doctor_departments")
    department = relationship("Department", back_populates="doctor_departments")

class Appointment(Base):
    __tablename__ = "Appointments"
    AppointmentId = Column(Integer, primary_key=True, index=True)
    PatientId = Column(Integer, ForeignKey("Users.UserId"))
    DoctorId = Column(Integer, ForeignKey("Users.UserId"), nullable=True)
    DepartmentId = Column(Integer, ForeignKey("Departments.DepartmentId"))
    Status = Column(Unicode(20), default="waiting")
    Priority = Column(Unicode(20), default="normal")
    Position = Column(Integer)
    ScheduledTime = Column(DateTime)
    CheckInTime = Column(DateTime)
    StartTime = Column(DateTime)
    EndTime = Column(DateTime)
    Symptoms = Column(UnicodeText)
    Diagnosis = Column(UnicodeText)
    Prescription = Column(UnicodeText)
    Notes = Column(UnicodeText)
    CreatedAt = Column(DateTime, default=datetime.utcnow)
    UpdatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Relationships
    patient = relationship("User", back_populates="appointments", foreign_keys=[PatientId])
    doctor = relationship("User", back_populates="doctor_appointments", foreign_keys=[DoctorId])
    department = relationship("Department", back_populates="appointments")
    medical_records = relationship("MedicalRecord", back_populates="appointment")

class MedicalRecord(Base):
    __tablename__ = "MedicalRecords"
    RecordId = Column(Integer, primary_key=True, index=True)
    AppointmentId = Column(Integer, ForeignKey("Appointments.AppointmentId"))
    BloodPressure = Column(Unicode(20))
    Temperature = Column(Unicode(10))
    Weight = Column(Unicode(10))
    Height = Column(Unicode(10))
    Pulse = Column(Unicode(10))
    Symptoms = Column(UnicodeText)
    Diagnosis = Column(UnicodeText)
    Treatment = Column(UnicodeText)
    Prescription = Column(UnicodeText)
    Notes = Column(UnicodeText)
    CreatedAt = Column(DateTime, default=datetime.utcnow)
    UpdatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Relationships
    appointment = relationship("Appointment", back_populates="medical_records")

class Notification(Base):
    __tablename__ = "Notifications"
    NotificationId = Column(Integer, primary_key=True, index=True)
    UserId = Column(Integer, ForeignKey("Users.UserId"))
    Title = Column(Unicode(200), nullable=False)
    Message = Column(UnicodeText, nullable=False)
    Type = Column(Unicode(20), default="info")
    IsRead = Column(Boolean, default=False)
    CreatedAt = Column(DateTime, default=datetime.utcnow)
    # Relationships
    user = relationship("User")

# Thêm các model Queue, QueueEntry, ServeHistory từ models.py
class Queue(Base):
    __tablename__ = "Queues"
    QueueId = Column(Integer, primary_key=True, index=True)
    ServiceName = Column(Unicode(100), nullable=False)
    CreatedAt = Column(DateTime, default=datetime.utcnow)
    entries = relationship("QueueEntry", back_populates="queue")

class QueueEntry(Base):
    __tablename__ = "QueueEntries"
    EntryId = Column(Integer, primary_key=True, index=True)
    QueueId = Column(Integer, ForeignKey("Queues.QueueId"), default=1)
    UserId = Column(Integer, ForeignKey("Users.UserId"), nullable=True)
    Status = Column(String(20), default="waiting")
    Position = Column(Integer)
    CreatedAt = Column(DateTime, default=datetime.utcnow)
    queue = relationship("Queue", back_populates="entries")
    user = relationship("User")
    history = relationship("ServeHistory", back_populates="queue_entry", uselist=False)

class ServeHistory(Base):
    __tablename__ = "ServeHistory"
    HistoryId = Column(Integer, primary_key=True, index=True)
    EntryId = Column(Integer, ForeignKey("QueueEntries.EntryId"))
    ServedAt = Column(DateTime, default=datetime.utcnow)
    queue_entry = relationship("QueueEntry", back_populates="history") 