import requests
import json

BASE_URL = "http://localhost:8000"

def test_queues():
    """Test getting queues"""
    try:
        response = requests.get(f"{BASE_URL}/queues")
        print(f"Queues API - Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error testing queues: {e}")

def test_stats():
    """Test getting stats"""
    try:
        response = requests.get(f"{BASE_URL}/stats")
        print(f"Stats API - Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error testing stats: {e}")

def test_add_queue_entry():
    """Test adding a queue entry"""
    try:
        data = {"QueueId": 1, "UserId": None}
        response = requests.post(f"{BASE_URL}/queue_entries", json=data)
        print(f"Add Queue Entry API - Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error testing add queue entry: {e}")

def test_queue_entries():
    """Test getting queue entries"""
    try:
        response = requests.get(f"{BASE_URL}/queue_entries")
        print(f"Queue Entries API - Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error testing queue entries: {e}")

if __name__ == "__main__":
    print("Testing Queue Management API...")
    print("=" * 50)
    
    test_queues()
    print("-" * 30)
    
    test_stats()
    print("-" * 30)
    
    test_queue_entries()
    print("-" * 30)
    
    test_add_queue_entry()
    print("-" * 30)
    
    test_queue_entries()
    print("=" * 50)
    print("Testing completed!") 