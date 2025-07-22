from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Sửa lại connection string cho đúng tên server/instance/database của bạn
SQLALCHEMY_DATABASE_URL = "mssql+pyodbc://@HP\\KANSQL/QueueManagement?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def drop_all_tables():
    from hospital_models import Base
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("All tables dropped.")

if __name__ == "__main__":
    drop_all_tables() 