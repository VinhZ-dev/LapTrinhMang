import database
import hospital_models as models
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def init_database():
    """Initialize the database with tables and default data"""
    
    # Create all tables
    print("Creating database tables...")
    models.Base.metadata.create_all(bind=database.engine)
    
    # Create a database session
    db = database.SessionLocal()
    
    try:
        # Check if admin user already exists
        admin_user = db.query(models.User).filter(models.User.Username == "admin1").first()
        
        if not admin_user:
            print("Creating admin user...")
            # Create admin user with proper password hash
            admin_user = models.User(
                Username="admin1",
                PasswordHash=get_password_hash("admin123"),  # Use a proper password
                Role="admin"
            )
            db.add(admin_user)
            db.commit()
            print("Admin user created successfully!")
        else:
            print("Admin user already exists.")
        
        # Create a default queue if none exists
        default_queue = db.query(models.Queue).filter(models.Queue.ServiceName == "Default Queue").first()
        
        if not default_queue:
            print("Creating default queue...")
            default_queue = models.Queue(ServiceName="Default Queue")
            db.add(default_queue)
            db.commit()
            print("Default queue created successfully!")
        else:
            print("Default queue already exists.")
            
        print("Database initialization completed!")
        
    except Exception as e:
        print(f"Error during database initialization: {e}")
        db.rollback()
    finally:
        db.close()

def check_sql_server_version():
    """Check SQL Server version"""
    try:
        from sqlalchemy import text
        db = database.engine.connect()
        result = db.execute(text("SELECT @@VERSION AS 'SQL Server Version'"))
        version = result.fetchone()
        print(f"SQL Server Version: {version[0]}")
        db.close()
        return True
    except Exception as e:
        print(f"Error checking SQL Server version: {e}")
        return False

if __name__ == "__main__":
    print("Starting database initialization...")
    
    # First check SQL Server connection
    if check_sql_server_version():
        # If connection is successful, initialize the database
        init_database()
    else:
        print("Cannot connect to SQL Server. Please check your connection settings.") 