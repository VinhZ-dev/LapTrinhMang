#!/usr/bin/env python3
"""
Script khởi tạo database và tạo dữ liệu mẫu
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# Thêm thư mục hiện tại vào path để import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import engine, SessionLocal
from hospital_models import Base, User, Department
from hospital_schemas import UserCreate

# Tạo thư mục data nếu chưa có
os.makedirs("data", exist_ok=True)

# Tạo tất cả bảng
def create_tables():
    print("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

# Tạo dữ liệu mẫu
def create_sample_data():
    print("Creating sample data...")
    db = SessionLocal()
    
    try:
        # Kiểm tra xem đã có dữ liệu chưa
        user_count = db.query(User).count()
        if user_count > 0:
            print("✅ Sample data already exists!")
            return True
        
        # Tạo mật khẩu hash
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Tạo admin user
        admin_user = User(
            Username="admin",
            PasswordHash=pwd_context.hash("admin123"),
            Email="admin@hospital.com",
            Phone="0123456789",
            FullName="Administrator",
            DateOfBirth="1990-01-01",
            Gender="Male",
            Address="123 Admin Street",
            Role="admin"
        )
        db.add(admin_user)
        
        # Tạo doctor user
        doctor_user = User(
            Username="doctor",
            PasswordHash=pwd_context.hash("doctor123"),
            Email="doctor@hospital.com",
            Phone="0987654321",
            FullName="Dr. John Doe",
            DateOfBirth="1985-05-15",
            Gender="Male",
            Address="456 Doctor Street",
            Role="doctor"
        )
        db.add(doctor_user)
        
        # Tạo receptionist user
        receptionist_user = User(
            Username="receptionist",
            PasswordHash=pwd_context.hash("receptionist123"),
            Email="receptionist@hospital.com",
            Phone="0555666777",
            FullName="Jane Smith",
            DateOfBirth="1992-08-20",
            Gender="Female",
            Address="789 Reception Street",
            Role="receptionist"
        )
        db.add(receptionist_user)
        
        # Tạo patient user
        patient_user = User(
            Username="patient",
            PasswordHash=pwd_context.hash("patient123"),
            Email="patient@email.com",
            Phone="0111222333",
            FullName="Patient User",
            DateOfBirth="1995-12-10",
            Gender="Male",
            Address="321 Patient Street",
            Role="patient"
        )
        db.add(patient_user)
        
        # Tạo các khoa
        departments = [
            Department(Name="Khoa Nội", Type="Internal", Description="Khoa nội tổng quát"),
            Department(Name="Khoa Ngoại", Type="Surgery", Description="Khoa ngoại tổng quát"),
            Department(Name="Khoa Nhi", Type="Pediatrics", Description="Khoa nhi"),
            Department(Name="Khoa Sản", Type="Obstetrics", Description="Khoa sản phụ khoa"),
            Department(Name="Khoa Mắt", Type="Ophthalmology", Description="Khoa mắt"),
            Department(Name="Khoa Tai Mũi Họng", Type="ENT", Description="Khoa tai mũi họng"),
        ]
        
        for dept in departments:
            db.add(dept)
        
        db.commit()
        print("✅ Sample data created successfully!")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating sample data: {e}")
        return False
    finally:
        db.close()

def main():
    print("🚀 Initializing Hospital Management System Database...")
    print("=" * 50)
    
    # Tạo bảng
    if not create_tables():
        print("❌ Failed to create tables. Exiting...")
        return
    
    # Tạo dữ liệu mẫu
    if not create_sample_data():
        print("❌ Failed to create sample data.")
        return
    
    print("=" * 50)
    print("✅ Database initialization completed successfully!")
    print("\n📋 Sample users created:")
    print("   Admin: username=admin, password=admin123")
    print("   Doctor: username=doctor, password=doctor123")
    print("   Receptionist: username=receptionist, password=receptionist123")
    print("   Patient: username=patient, password=patient123")
    print("\n🚀 You can now start the application with: uvicorn main:app --reload")

if __name__ == "__main__":
    main() 