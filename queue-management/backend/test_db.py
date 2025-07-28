#!/usr/bin/env python3
"""
Test kết nối database
"""

try:
    from database import test_connection
    print("Testing database connection...")
    test_connection()
except Exception as e:
    print(f"Error: {e}") 