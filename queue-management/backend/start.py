#!/usr/bin/env python3
"""
Script đơn giản để chạy Hospital Management System
"""

import os
import sys
import subprocess

def main():
    print("🏥 Hospital Management System")
    print("=" * 40)
    
    # Kiểm tra xem có đang ở đúng thư mục không
    if not os.path.exists("hospital_api.py"):
        print("❌ Error: Please run this script from the backend directory")
        print("   cd queue-management/backend")
        return
    
    # Tạo thư mục data nếu chưa có
    os.makedirs("data", exist_ok=True)
    
    print("🚀 Starting server...")
    print("📱 Frontend: http://127.0.0.1:5502/queue-management/frontend/hospital/login.html")
    print("🔧 Backend: http://127.0.0.1:8000")
    print("📚 API Docs: http://127.0.0.1:8000/docs")
    print("=" * 50)
    
    try:
        # Chạy uvicorn
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "hospital_api:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 