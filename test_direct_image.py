#!/usr/bin/env python3
"""
Quick test for image moderation service
"""

import requests
import io
from PIL import Image

def create_test_image():
    """Create a simple test image"""
    img = Image.new('RGB', (100, 100), color='blue')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes

def test_direct_service():
    """Test image service directly"""
    print("Testing image moderation service directly...")
    
    # Test health
    try:
        response = requests.get("http://localhost:8002/health")
        print(f"Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")
        return
    
    # Test categories
    try:
        response = requests.get("http://localhost:8002/api/v1/categories")
        print(f"Categories: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Categories failed: {e}")
    
    # Test moderation endpoint
    try:
        img_bytes = create_test_image()
        files = {'file': ('test.jpg', img_bytes, 'image/jpeg')}
        response = requests.post("http://localhost:8002/api/v1/moderate", files=files)
        print(f"Moderation: {response.status_code}")
        if response.status_code == 200:
            print(f"Result: {response.json()}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Moderation failed: {e}")

if __name__ == "__main__":
    test_direct_service()
