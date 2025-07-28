from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Kết nối SQL Server database
SQLALCHEMY_DATABASE_URL = "mssql+pyodbc://@HP\\KANSQL/QueueManagement?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"

# Tạo engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False  # Set to True để debug SQL queries
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def test_connection():
    """Test kết nối database"""
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT @@VERSION AS 'SQL Server Version'"))
            version = result.fetchone()
            print(f"✅ Connected to SQL Server: {version[0]}")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def create_tables():
    """Tạo tất cả bảng nếu chưa tồn tại"""
    try:
        from hospital_models import Base
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")

if __name__ == "__main__":
    test_connection() 