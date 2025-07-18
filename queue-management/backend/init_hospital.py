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
            {
                "Name": "Emergency Department",
                "Type": "emergency",
                "Description": "24/7 emergency medical care",
                "Location": "Ground Floor",
                "Floor": "G",
                "RoomNumber": "ER-01"
            },
            {
                "Name": "Cardiology",
                "Type": "cardiology",
                "Description": "Heart and cardiovascular care",
                "Location": "First Floor",
                "Floor": "1",
                "RoomNumber": "CARD-01"
            },
            {
                "Name": "Neurology",
                "Type": "neurology",
                "Description": "Brain and nervous system care",
                "Location": "Second Floor",
                "Floor": "2",
                "RoomNumber": "NEURO-01"
            },
            {
                "Name": "Pediatrics",
                "Type": "pediatrics",
                "Description": "Children's healthcare",
                "Location": "Third Floor",
                "Floor": "3",
                "RoomNumber": "PED-01"
            },
            {
                "Name": "Orthopedics",
                "Type": "orthopedics",
                "Description": "Bone and joint care",
                "Location": "Fourth Floor",
                "Floor": "4",
                "RoomNumber": "ORTHO-01"
            },
            {
                "Name": "General Medicine",
                "Type": "general",
                "Description": "General medical care",
                "Location": "Fifth Floor",
                "Floor": "5",
                "RoomNumber": "GEN-01"
            }
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
        
        # Create admin user
        admin_user = db.query(models.User).filter(models.User.Username == "admin").first()
        if not admin_user:
            admin_user = models.User(
                Username="admin",
                PasswordHash=get_password_hash("admin123"),
                Email="admin@hospital.com",
                Phone="0123456789",
                FullName="Hospital Administrator",
                Role="admin",
                IsActive=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            print("Created admin user")
        else:
            print("Admin user already exists")
        
        # Create doctors
        doctors_data = [
            {
                "Username": "dr.smith",
                "FullName": "Dr. John Smith",
                "Email": "dr.smith@hospital.com",
                "Phone": "0123456781",
                "Role": "doctor",
                "DepartmentId": 1  # Emergency
            },
            {
                "Username": "dr.johnson",
                "FullName": "Dr. Sarah Johnson",
                "Email": "dr.johnson@hospital.com",
                "Phone": "0123456782",
                "Role": "doctor",
                "DepartmentId": 2  # Cardiology
            },
            {
                "Username": "dr.williams",
                "FullName": "Dr. Michael Williams",
                "Email": "dr.williams@hospital.com",
                "Phone": "0123456783",
                "Role": "doctor",
                "DepartmentId": 3  # Neurology
            },
            {
                "Username": "dr.brown",
                "FullName": "Dr. Emily Brown",
                "Email": "dr.brown@hospital.com",
                "Phone": "0123456784",
                "Role": "doctor",
                "DepartmentId": 4  # Pediatrics
            },
            {
                "Username": "dr.davis",
                "FullName": "Dr. David Davis",
                "Email": "dr.davis@hospital.com",
                "Phone": "0123456785",
                "Role": "doctor",
                "DepartmentId": 5  # Orthopedics
            },
            {
                "Username": "dr.miller",
                "FullName": "Dr. Lisa Miller",
                "Email": "dr.miller@hospital.com",
                "Phone": "0123456786",
                "Role": "doctor",
                "DepartmentId": 6  # General Medicine
            }
        ]
        
        doctors = []
        for doctor_data in doctors_data:
            existing_doctor = db.query(models.User).filter(
                models.User.Username == doctor_data["Username"]
            ).first()
            
            if not existing_doctor:
                doctor = models.User(
                    Username=doctor_data["Username"],
                    PasswordHash=get_password_hash("doctor123"),
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
        
        # Create nurses
        nurses_data = [
            {
                "Username": "nurse.anderson",
                "FullName": "Nurse Jennifer Anderson",
                "Email": "nurse.anderson@hospital.com",
                "Phone": "0123456791",
                "Role": "nurse"
            },
            {
                "Username": "nurse.taylor",
                "FullName": "Nurse Robert Taylor",
                "Email": "nurse.taylor@hospital.com",
                "Phone": "0123456792",
                "Role": "nurse"
            },
            {
                "Username": "nurse.thomas",
                "FullName": "Nurse Maria Thomas",
                "Email": "nurse.thomas@hospital.com",
                "Phone": "0123456793",
                "Role": "nurse"
            }
        ]
        
        for nurse_data in nurses_data:
            existing_nurse = db.query(models.User).filter(
                models.User.Username == nurse_data["Username"]
            ).first()
            
            if not existing_nurse:
                nurse = models.User(
                    Username=nurse_data["Username"],
                    PasswordHash=get_password_hash("nurse123"),
                    Email=nurse_data["Email"],
                    Phone=nurse_data["Phone"],
                    FullName=nurse_data["FullName"],
                    Role=nurse_data["Role"],
                    IsActive=True
                )
                db.add(nurse)
                db.commit()
                print(f"Created nurse: {nurse.FullName}")
            else:
                print(f"Nurse already exists: {existing_nurse.FullName}")
        
        # Create receptionist
        receptionist = db.query(models.User).filter(models.User.Username == "receptionist").first()
        if not receptionist:
            receptionist = models.User(
                Username="receptionist",
                PasswordHash=get_password_hash("reception123"),
                Email="reception@hospital.com",
                Phone="0123456700",
                FullName="Hospital Receptionist",
                Role="receptionist",
                IsActive=True
            )
            db.add(receptionist)
            db.commit()
            print("Created receptionist")
        else:
            print("Receptionist already exists")
        
        # Create sample patients
        patients_data = [
            {
                "Username": "patient.001",
                "FullName": "Alice Johnson",
                "Email": "alice.johnson@email.com",
                "Phone": "0987654321",
                "DateOfBirth": datetime(1985, 5, 15),
                "Gender": "Female"
            },
            {
                "Username": "patient.002",
                "FullName": "Bob Smith",
                "Email": "bob.smith@email.com",
                "Phone": "0987654322",
                "DateOfBirth": datetime(1978, 8, 22),
                "Gender": "Male"
            },
            {
                "Username": "patient.003",
                "FullName": "Carol Davis",
                "Email": "carol.davis@email.com",
                "Phone": "0987654323",
                "DateOfBirth": datetime(1992, 3, 10),
                "Gender": "Female"
            },
            {
                "Username": "patient.004",
                "FullName": "David Wilson",
                "Email": "david.wilson@email.com",
                "Phone": "0987654324",
                "DateOfBirth": datetime(1965, 11, 5),
                "Gender": "Male"
            },
            {
                "Username": "patient.005",
                "FullName": "Eva Brown",
                "Email": "eva.brown@email.com",
                "Phone": "0987654325",
                "DateOfBirth": datetime(1988, 7, 18),
                "Gender": "Female"
            }
        ]
        
        patients = []
        for patient_data in patients_data:
            existing_patient = db.query(models.User).filter(
                models.User.Username == patient_data["Username"]
            ).first()
            
            if not existing_patient:
                patient = models.User(
                    Username=patient_data["Username"],
                    PasswordHash=get_password_hash("patient123"),
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
            "Headache and fever",
            "Chest pain",
            "Back pain",
            "Fever and cough",
            "Abdominal pain",
            "Dizziness",
            "Shortness of breath",
            "Joint pain"
        ]
        
        priorities = ["low", "normal", "high", "emergency"]
        
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