#!/usr/bin/env python3
"""
Simple test for image moderation service
"""

import requests
import json

def test_image_service():
    """Test image service endpoints"""
    base_url = "http://localhost:8002"
    
    # Test health
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"Health: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Health failed: {e}")
        return False
    
    # Test categories
    print("\nTesting categories endpoint...")
    try:
        response = requests.get(f"{base_url}/api/v1/categories", timeout=5)
        print(f"Categories: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Categories failed: {e}")
    
    # Test supported formats
    print("\nTesting supported formats endpoint...")
    try:
        response = requests.get(f"{base_url}/api/v1/supported-formats", timeout=5)
        print(f"Formats: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Formats failed: {e}")
    
    return True

if __name__ == "__main__":
    test_image_service()
