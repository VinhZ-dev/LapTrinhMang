#!/usr/bin/env python3
"""
Script chạy ứng dụng sạch sẽ không có thông báo debug
"""

import os
import sys
import subprocess

def main():
    # Tạo thư mục data nếu chưa có
    os.makedirs("data", exist_ok=True)
    
    # Chạy uvicorn với log level error để ẩn thông báo
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "hospital_api:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload",
            "--log-level", "error"
        ])
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main() 