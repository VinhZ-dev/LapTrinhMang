from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "Users"
    UserId = Column(Integer, primary_key=True, index=True)
    Username = Column(String(50), unique=True, index=True, nullable=False)
    PasswordHash = Column(String(255), nullable=False)
    Role = Column(String(20), nullable=False)
    Email = Column(String(100))
    Phone = Column(String(20))
    FullName = Column(String(100), nullable=False)
    DateOfBirth = Column(DateTime)
    Gender = Column(String(10))
    Address = Column(Text)
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
    Name = Column(String(100), nullable=False)
    Type = Column(String(20), nullable=False)
    Description = Column(Text)
    Location = Column(String(100))
    Floor = Column(String(10))
    RoomNumber = Column(String(20))
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
    Status = Column(String(20), default="waiting")
    Priority = Column(String(20), default="normal")
    Position = Column(Integer)
    ScheduledTime = Column(DateTime)
    CheckInTime = Column(DateTime)
    StartTime = Column(DateTime)
    EndTime = Column(DateTime)
    Symptoms = Column(Text)
    Diagnosis = Column(Text)
    Prescription = Column(Text)
    Notes = Column(Text)
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
    BloodPressure = Column(String(20))
    Temperature = Column(String(10))
    Weight = Column(String(10))
    Height = Column(String(10))
    Pulse = Column(String(10))
    Symptoms = Column(Text)
    Diagnosis = Column(Text)
    Treatment = Column(Text)
    Prescription = Column(Text)
    Notes = Column(Text)
    CreatedAt = Column(DateTime, default=datetime.utcnow)
    UpdatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Relationships
    appointment = relationship("Appointment", back_populates="medical_records")

class Notification(Base):
    __tablename__ = "Notifications"
    NotificationId = Column(Integer, primary_key=True, index=True)
    UserId = Column(Integer, ForeignKey("Users.UserId"))
    Title = Column(String(200), nullable=False)
    Message = Column(Text, nullable=False)
    Type = Column(String(20), default="info")
    IsRead = Column(Boolean, default=False)
    CreatedAt = Column(DateTime, default=datetime.utcnow)
    # Relationships
    user = relationship("User") 