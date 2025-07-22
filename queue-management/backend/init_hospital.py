import database
import hospital_models as models
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, timedelta
import random

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def init_hospital_database():
    """Initialize the hospital database with sample data"""
    
    # Create all tables
    print("Creating hospital database tables...")
    models.Base.metadata.create_all(bind=database.engine)
    
    # Create a database session
    db = database.SessionLocal()
    
    try:
        # Create departments
        departments_data = [
            {"Name": "Khoa Nội tổng hợp", "Type": "noi-tong-hop", "Description": "Khám và điều trị nội tổng hợp", "Location": "Tầng 1", "Floor": "1", "RoomNumber": "NOI-01"},
            {"Name": "Khoa Nhi", "Type": "nhi", "Description": "Chăm sóc sức khỏe trẻ em", "Location": "Tầng 2", "Floor": "2", "RoomNumber": "NHI-01"},
            {"Name": "Khoa Sản", "Type": "san", "Description": "Chăm sóc sức khỏe phụ nữ", "Location": "Tầng 3", "Floor": "3", "RoomNumber": "SAN-01"},
            {"Name": "Khoa Ngoại", "Type": "ngoai", "Description": "Phẫu thuật và điều trị ngoại khoa", "Location": "Tầng 4", "Floor": "4", "RoomNumber": "NGOAI-01"},
            {"Name": "Khoa Cấp cứu", "Type": "capcuu", "Description": "Chăm sóc y tế khẩn cấp 24/7", "Location": "Tầng trệt", "Floor": "G", "RoomNumber": "CC-01"}
        ]
        
        departments = []
        for dept_data in departments_data:
            existing_dept = db.query(models.Department).filter(
                models.Department.Name == dept_data["Name"]
            ).first()
            
            if not existing_dept:
                dept = models.Department(**dept_data)
                db.add(dept)
                db.commit()
                db.refresh(dept)
                departments.append(dept)
                print(f"Created department: {dept.Name}")
            else:
                departments.append(existing_dept)
                print(f"Department already exists: {existing_dept.Name}")
        
        # Chỉ tạo 1 admin gốc
        admin_user = db.query(models.User).filter(models.User.Username == "kan111").first()
        if not admin_user:
            admin_user = models.User(
                Username="kan111",
                PasswordHash=get_password_hash("111111"),
                Email="admin@benhvien.com",
                Phone="0909000000",
                FullName="Quản trị viên gốc",
                Role="admin",
                IsActive=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            print("Đã tạo admin gốc")
        else:
            print("Admin gốc đã tồn tại")
        
        # Chỉ tạo 5 bác sĩ
        doctors_data = [
            {"Username": "bs.nguyen", "FullName": "BS. Nguyễn Văn A", "Email": "nguyenvana@benhvien.com", "Phone": "0901000001", "Role": "doctor", "DepartmentId": 1},
            {"Username": "bs.tran", "FullName": "BS. Trần Thị B", "Email": "tranthib@benhvien.com", "Phone": "0901000002", "Role": "doctor", "DepartmentId": 2},
            {"Username": "bs.le", "FullName": "BS. Lê Văn C", "Email": "levanc@benhvien.com", "Phone": "0901000003", "Role": "doctor", "DepartmentId": 3},
            {"Username": "bs.pham", "FullName": "BS. Phạm Thị D", "Email": "phamthid@benhvien.com", "Phone": "0901000004", "Role": "doctor", "DepartmentId": 4},
            {"Username": "bs.hoang", "FullName": "BS. Hoàng Văn E", "Email": "hoangvane@benhvien.com", "Phone": "0901000005", "Role": "doctor", "DepartmentId": 5}
        ]
        
        doctors = []
        for doctor_data in doctors_data:
            existing_doctor = db.query(models.User).filter(
                models.User.Username == doctor_data["Username"]
            ).first()
            
            if not existing_doctor:
                doctor = models.User(
                    Username=doctor_data["Username"],
                    PasswordHash=get_password_hash("111111"),
                    Email=doctor_data["Email"],
                    Phone=doctor_data["Phone"],
                    FullName=doctor_data["FullName"],
                    Role=doctor_data["Role"],
                    IsActive=True
                )
                db.add(doctor)
                db.commit()
                db.refresh(doctor)
                doctors.append(doctor)
                
                # Assign doctor to department
                doctor_dept = models.DoctorDepartment(
                    DoctorId=doctor.UserId,
                    DepartmentId=doctor_data["DepartmentId"],
                    IsPrimary=True
                )
                db.add(doctor_dept)
                db.commit()
                
                print(f"Created doctor: {doctor.FullName}")
            else:
                doctors.append(existing_doctor)
                print(f"Doctor already exists: {existing_doctor.FullName}")
        
        # Chỉ tạo 5 bệnh nhân
        patients_data = [
            {"Username": "bn.001", "FullName": "Nguyễn Thị Mai", "Email": "mainguyen@email.com", "Phone": "0911000001", "DateOfBirth": datetime(1990, 1, 1), "Gender": "Nữ"},
            {"Username": "bn.002", "FullName": "Trần Văn Bình", "Email": "binhtran@email.com", "Phone": "0911000002", "DateOfBirth": datetime(1985, 2, 2), "Gender": "Nam"},
            {"Username": "bn.003", "FullName": "Lê Thị Cúc", "Email": "cuclt@email.com", "Phone": "0911000003", "DateOfBirth": datetime(2000, 3, 3), "Gender": "Nữ"},
            {"Username": "bn.004", "FullName": "Phạm Văn Dũng", "Email": "dungpham@email.com", "Phone": "0911000004", "DateOfBirth": datetime(1975, 4, 4), "Gender": "Nam"},
            {"Username": "bn.005", "FullName": "Hoàng Thị Hạnh", "Email": "hanhhoang@email.com", "Phone": "0911000005", "DateOfBirth": datetime(1995, 5, 5), "Gender": "Nữ"}
        ]
        
        patients = []
        for patient_data in patients_data:
            existing_patient = db.query(models.User).filter(
                models.User.Username == patient_data["Username"]
            ).first()
            
            if not existing_patient:
                patient = models.User(
                    Username=patient_data["Username"],
                    PasswordHash=get_password_hash("111111"),
                    Email=patient_data["Email"],
                    Phone=patient_data["Phone"],
                    FullName=patient_data["FullName"],
                    DateOfBirth=patient_data["DateOfBirth"],
                    Gender=patient_data["Gender"],
                    Role="patient",
                    IsActive=True
                )
                db.add(patient)
                db.commit()
                db.refresh(patient)
                patients.append(patient)
                print(f"Created patient: {patient.FullName}")
            else:
                patients.append(existing_patient)
                print(f"Patient already exists: {existing_patient.FullName}")
        
        # Create sample appointments
        symptoms_list = [
            "Đau đầu, sốt cao",
            "Đau ngực, khó thở",
            "Đau lưng",
            "Sốt, ho",
            "Đau bụng",
            "Chóng mặt",
            "Khó thở, mệt mỏi",
            "Đau khớp, sưng tấy"
        ]
        
        priorities = ["thấp", "bình thường", "cao", "khẩn cấp"]
        
        for i, patient in enumerate(patients):
            # Create 1-3 appointments per patient
            num_appointments = random.randint(1, 3)
            for j in range(num_appointments):
                department = random.choice(departments)
                doctor = random.choice([d for d in doctors if d.UserId in [
                    dd.DoctorId for dd in db.query(models.DoctorDepartment).filter(
                        models.DoctorDepartment.DepartmentId == department.DepartmentId
                    ).all()
                ]])
                
                appointment = models.Appointment(
                    PatientId=patient.UserId,
                    DoctorId=doctor.UserId if doctor else None,
                    DepartmentId=department.DepartmentId,
                    Status=random.choice(["waiting", "in_progress", "completed"]),
                    Priority=random.choice(priorities),
                    Position=random.randint(1, 10),
                    Symptoms=random.choice(symptoms_list),
                    ScheduledTime=datetime.utcnow() + timedelta(hours=random.randint(1, 24))
                )
                db.add(appointment)
        
        db.commit()
        print("Created sample appointments")
        
        print("Hospital database initialization completed successfully!")
        
    except Exception as e:
        print(f"Error during database initialization: {e}")
        db.rollback()
    finally:
        db.close()

def check_sql_server_version():
    """Check SQL Server version"""
    try:
        db = database.engine.connect()
        from sqlalchemy import text
        result = db.execute(text("SELECT @@VERSION AS 'SQL Server Version'"))
        version = result.fetchone()
        print(f"SQL Server Version: {version[0]}")
        db.close()
        return True
    except Exception as e:
        print(f"Error checking SQL Server version: {e}")
        return False

if __name__ == "__main__":
    print("Starting Hospital Queue Management System initialization...")
    
    # First check SQL Server connection
    if check_sql_server_version():
        # If connection is successful, initialize the database
        init_hospital_database()
    else:
        print("Cannot connect to SQL Server. Please check your connection settings.") 