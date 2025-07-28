#!/usr/bin/env python3
"""
Script để restart server với database mới
"""

import os
import sys
import subprocess
import time

def main():
    print("🔄 Restarting Hospital Management System...")
    
    # Xóa database cũ
    if os.path.exists("data"):
        try:
            import shutil
            shutil.rmtree("data")
            print("✅ Removed old database")
        except Exception as e:
            print(f"⚠️ Could not remove old database: {e}")
    
    # Tạo thư mục data mới
    os.makedirs("data", exist_ok=True)
    print("✅ Created new data directory")
    
    print("🚀 Starting server with new database...")
    print("📱 Frontend: http://127.0.0.1:5502/queue-management/frontend/hospital/login.html")
    print("🔧 Backend: http://127.0.0.1:8000")
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