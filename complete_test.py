#!/usr/bin/env python3
"""
Complete System Integration Test
Tests the entire content moderation system through the API Gateway
"""

import requests
import json
import io
from PIL import Image

def create_test_image(color='blue', size=(100, 100)):
    """Create a test image with specified color"""
    img = Image.new('RGB', size, color=color)
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes

def test_complete_system():
    """Test the complete content moderation system"""
    api_gateway_url = "http://localhost:8000"
    
    print("🚀 AI Content Moderation System - Complete Integration Test")
    print("=" * 70)
    
    # Test 1: API Gateway Health
    print("\n1. Testing API Gateway Health...")
    try:
        response = requests.get(f"{api_gateway_url}/health")
        print(f"   ✅ API Gateway: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"   ❌ API Gateway failed: {e}")
        return False
    
    # Test 2: Service Status Check
    print("\n2. Testing Service Status...")
    try:
        response = requests.get(f"{api_gateway_url}/status")
        status = response.json()
        print(f"   📊 System Status: {json.dumps(status, indent=6)}")
    except Exception as e:
        print(f"   ❌ Status check failed: {e}")
    
    # Test 3: Text Moderation via Gateway
    print("\n3. Testing Text Moderation via API Gateway...")
    
    test_texts = [
        {"text": "Hello, this is a nice day!", "expected": True},
        {"text": "This damn thing is shit!", "expected": False},
        {"text": "I love programming and technology!", "expected": True},
        {"text": "You are a fucking idiot!", "expected": False}
    ]
    
    for i, test_case in enumerate(test_texts, 1):
        try:
            payload = {
                "text": test_case["text"],
                "user_id": f"test_user_{i}",
                "content_id": f"text_{i}"
            }
            response = requests.post(f"{api_gateway_url}/moderate/text", json=payload)
            
            if response.status_code == 200:
                result = response.json()
                appropriate = result["is_appropriate"]
                expected = test_case["expected"]
                status = "✅" if appropriate == expected else "⚠️"
                
                print(f"   {status} Text {i}: '{test_case['text'][:30]}...'")
                print(f"      - Appropriate: {appropriate} (Expected: {expected})")
                print(f"      - Confidence: {result['confidence_score']:.2f}")
                print(f"      - Categories: {result['flagged_categories']}")
            else:
                print(f"   ❌ Text {i} failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"   ❌ Text {i} error: {e}")
    
    # Test 4: Image Moderation via Gateway
    print("\n4. Testing Image Moderation via API Gateway...")
    
    test_images = [
        {"name": "blue_safe.jpg", "color": "blue", "expected": True},
        {"name": "red_warning.jpg", "color": "red", "expected": True},  # Red might trigger violence detection
        {"name": "green_safe.jpg", "color": "green", "expected": True}
    ]
    
    for i, test_case in enumerate(test_images, 1):
        try:
            img_bytes = create_test_image(test_case["color"])
            files = {'file': (test_case["name"], img_bytes, 'image/jpeg')}
            data = {
                'user_id': f'test_user_{i}',
                'content_id': f'image_{i}'
            }
            
            response = requests.post(f"{api_gateway_url}/moderate/image", files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                appropriate = result["is_appropriate"]
                
                print(f"   ✅ Image {i}: {test_case['name']} ({test_case['color']})")
                print(f"      - Appropriate: {appropriate}")
                print(f"      - Confidence: {result['confidence_score']:.2f}")
                print(f"      - Categories: {result['flagged_categories']}")
                print(f"      - Size: {result['image_info']['width']}x{result['image_info']['height']}")
            else:
                print(f"   ❌ Image {i} failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"   ❌ Image {i} error: {e}")
    
    # Test 5: Batch Processing
    print("\n5. Testing Batch Text Processing...")
    try:
        batch_texts = [
            "This is a great product!",
            "This fucking sucks!",
            "I love this service!"
        ]
        
        payload = {"texts": batch_texts}
        response = requests.post(f"{api_gateway_url}/moderate/batch", json=payload)
        
        if response.status_code == 200:
            results = response.json()
            print(f"   ✅ Batch processing successful:")
            for i, result in enumerate(results["results"], 1):
                print(f"      Text {i}: Appropriate={result['is_appropriate']}, "
                      f"Confidence={result['confidence_score']:.2f}")
        else:
            print(f"   ❌ Batch processing failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Batch processing error: {e}")
    
    # Test 6: Database Analytics
    print("\n6. Testing Database Analytics...")
    try:
        response = requests.get(f"{api_gateway_url}/analytics/summary")
        if response.status_code == 200:
            analytics = response.json()
            print(f"   ✅ Analytics retrieved:")
            print(f"      - Total requests: {analytics.get('total_requests', 'N/A')}")
            print(f"      - Flagged content: {analytics.get('flagged_content', 'N/A')}")
            print(f"      - Text requests: {analytics.get('text_requests', 'N/A')}")
            print(f"      - Image requests: {analytics.get('image_requests', 'N/A')}")
        else:
            print(f"   ⚠️ Analytics not available: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️ Analytics error: {e}")
    
    print("\n" + "=" * 70)
    print("🎉 Integration Test Complete!")
    print("=" * 70)
    
    return True

if __name__ == "__main__":
    test_complete_system()
