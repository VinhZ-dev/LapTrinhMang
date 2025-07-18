from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# User
class UserBase(BaseModel):
    Username: str
    Email: Optional[str] = None
    Phone: Optional[str] = None
    FullName: str
    DateOfBirth: Optional[datetime] = None
    Gender: Optional[str] = None
    Address: Optional[str] = None
    Role: str

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    UserId: int
    IsActive: bool
    CreatedAt: datetime
    UpdatedAt: datetime
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    FullName: Optional[str] = None
    Email: Optional[str] = None
    Phone: Optional[str] = None
    DateOfBirth: Optional[datetime] = None
    Gender: Optional[str] = None
    Address: Optional[str] = None

# Department
class DepartmentBase(BaseModel):
    Name: str
    Type: str
    Description: Optional[str] = None
    Location: Optional[str] = None
    Floor: Optional[str] = None
    RoomNumber: Optional[str] = None

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentOut(DepartmentBase):
    DepartmentId: int
    IsActive: bool
    CreatedAt: datetime
    UpdatedAt: datetime
    class Config:
        from_attributes = True

# DoctorDepartment
class DoctorDepartmentBase(BaseModel):
    DoctorId: int
    DepartmentId: int
    IsPrimary: bool = False

class DoctorDepartmentCreate(DoctorDepartmentBase):
    pass

class DoctorDepartmentOut(DoctorDepartmentBase):
    Id: int
    CreatedAt: datetime
    class Config:
        from_attributes = True

# Appointment
class AppointmentBase(BaseModel):
    PatientId: int
    DoctorId: Optional[int] = None
    DepartmentId: int
    Status: str = "waiting"
    Priority: str = "normal"
    ScheduledTime: Optional[datetime] = None
    Symptoms: Optional[str] = None

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentOut(AppointmentBase):
    AppointmentId: int
    Position: Optional[int] = None
    CheckInTime: Optional[datetime] = None
    StartTime: Optional[datetime] = None
    EndTime: Optional[datetime] = None
    Diagnosis: Optional[str] = None
    Prescription: Optional[str] = None
    Notes: Optional[str] = None
    CreatedAt: datetime
    UpdatedAt: datetime
    class Config:
        from_attributes = True

# MedicalRecord
class MedicalRecordBase(BaseModel):
    AppointmentId: int
    BloodPressure: Optional[str] = None
    Temperature: Optional[str] = None
    Weight: Optional[str] = None
    Height: Optional[str] = None
    Pulse: Optional[str] = None
    Symptoms: Optional[str] = None
    Diagnosis: Optional[str] = None
    Treatment: Optional[str] = None
    Prescription: Optional[str] = None
    Notes: Optional[str] = None

class MedicalRecordCreate(MedicalRecordBase):
    pass

class MedicalRecordOut(MedicalRecordBase):
    RecordId: int
    CreatedAt: datetime
    UpdatedAt: datetime
    class Config:
        from_attributes = True

# Notification
class NotificationBase(BaseModel):
    UserId: int
    Title: str
    Message: str
    Type: str = "info"

class NotificationCreate(NotificationBase):
    pass

class NotificationOut(NotificationBase):
    NotificationId: int
    IsRead: bool
    CreatedAt: datetime
    class Config:
        from_attributes = True

# Auth
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserOut 