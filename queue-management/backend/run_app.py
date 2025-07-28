#!/usr/bin/env python3
"""
Script để chạy ứng dụng Hospital Management System
"""

import os
import sys
import subprocess
import time

def check_dependencies():
    """Kiểm tra các dependencies cần thiết"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        "fastapi",
        "uvicorn", 
        "sqlalchemy",
        "pydantic",
        "passlib",
        "python-jose",
        "websockets",
        "python-multipart"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
            print("✅ Dependencies installed successfully!")
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies. Please install manually:")
            print(f"pip install {' '.join(missing_packages)}")
            return False
    else:
        print("✅ All dependencies are installed!")
    
    return True

def initialize_database():
    """Khởi tạo database"""
    print("🗄️ Initializing database...")
    try:
        from init_db import main as init_db_main
        init_db_main()
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def start_server():
    """Khởi động server"""
    print("🚀 Starting Hospital Management System...")
    print("=" * 50)
    print("📱 Frontend URL: http://127.0.0.1:5502/queue-management/frontend/hospital/login.html")
    print("🔧 Backend API: http://127.0.0.1:8000")
    print("📚 API Docs: http://127.0.0.1:8000/docs")
    print("=" * 50)
    
    try:
        # Chạy uvicorn server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "hospital_api:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")

def main():
    print("🏥 Hospital Management System")
    print("=" * 40)
    
    # Kiểm tra dependencies
    if not check_dependencies():
        return
    
    # Khởi tạo database
    if not initialize_database():
        print("⚠️ Continuing without database initialization...")
    
    # Khởi động server
    start_server()

if __name__ == "__main__":
    main() 