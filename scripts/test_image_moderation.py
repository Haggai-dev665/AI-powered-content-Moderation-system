#!/usr/bin/env python3
"""
Test script for image moderation functionality.
Creates sample images and tests the image moderation service.
"""

import os
import sys
import numpy as np
import cv2
import requests
import io
from PIL import Image, ImageDraw, ImageFont
import base64

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_test_images():
    """Create sample test images for moderation testing."""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # Create a simple safe image (blue gradient)
    safe_image = np.zeros((300, 300, 3), dtype=np.uint8)
    for i in range(300):
        safe_image[i, :] = [i//2, 100, 255 - i//2]  # Blue gradient
    cv2.imwrite(os.path.join(data_dir, 'safe_image.jpg'), safe_image)
    
    # Create an image with skin-like colors (might trigger skin detection)
    skin_image = np.zeros((300, 300, 3), dtype=np.uint8)
    # Skin-like RGB values
    skin_color = [220, 180, 140]  # Light skin tone
    skin_image[:] = skin_color
    cv2.imwrite(os.path.join(data_dir, 'skin_tone_image.jpg'), skin_image)
    
    # Create an image with red content (might trigger violence detection)
    red_image = np.zeros((300, 300, 3), dtype=np.uint8)
    red_image[:] = [0, 0, 255]  # Red in BGR format
    cv2.imwrite(os.path.join(data_dir, 'red_image.jpg'), red_image)
    
    # Create a gray image with simple shapes
    gray_image = np.full((300, 300, 3), 128, dtype=np.uint8)
    cv2.rectangle(gray_image, (50, 50), (250, 250), (200, 200, 200), -1)
    cv2.circle(gray_image, (150, 150), 50, (100, 100, 100), -1)
    cv2.imwrite(os.path.join(data_dir, 'shapes_image.jpg'), gray_image)
    
    # Create a noise image
    noise_image = np.random.randint(0, 256, (300, 300, 3), dtype=np.uint8)
    cv2.imwrite(os.path.join(data_dir, 'noise_image.jpg'), noise_image)
    
    print(f"Created test images in {data_dir}")
    return data_dir

def image_to_base64(image_path):
    """Convert image file to base64 string."""
    with open(image_path, 'rb') as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

def test_image_moderation_api():
    """Test the image moderation API with sample images."""
    print("Testing Image Moderation API...")
    
    # Create test images
    data_dir = create_test_images()
    
    # Test images
    test_images = [
        'safe_image.jpg',
        'skin_tone_image.jpg', 
        'red_image.jpg',
        'shapes_image.jpg',
        'noise_image.jpg'
    ]
    
    # Test through API Gateway
    api_gateway_url = "http://localhost:8000"
    
    for image_name in test_images:
        image_path = os.path.join(data_dir, image_name)
        
        print(f"\n--- Testing {image_name} ---")
        
        try:
            # Test with file upload
            with open(image_path, 'rb') as img_file:
                files = {'file': (image_name, img_file, 'image/jpeg')}
                response = requests.post(f"{api_gateway_url}/moderate/image", files=files)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Status: {result['status']}")
                print(f"   Explicit Content: {result['explicit_content']:.3f}")
                print(f"   Violence: {result['violence']:.3f}")
                print(f"   Weapons: {result['weapons']:.3f}")
                print(f"   Safe: {result['is_safe']}")
                print(f"   Confidence: {result['confidence']:.3f}")
                if result['detected_issues']:
                    print(f"   Issues: {', '.join(result['detected_issues'])}")
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
    
    # Test direct image service
    print("\n" + "="*50)
    print("Testing Image Service Directly...")
    
    image_service_url = "http://localhost:8002"
    
    for image_name in test_images:
        image_path = os.path.join(data_dir, image_name)
        
        print(f"\n--- Testing {image_name} (Direct Service) ---")
        
        try:
            with open(image_path, 'rb') as img_file:
                files = {'file': (image_name, img_file, 'image/jpeg')}
                response = requests.post(f"{image_service_url}/moderate", files=files)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Status: {result['status']}")
                print(f"   Explicit Content: {result['explicit_content']:.3f}")
                print(f"   Violence: {result['violence']:.3f}")
                print(f"   Weapons: {result['weapons']:.3f}")
                print(f"   Safe: {result['is_safe']}")
                print(f"   Confidence: {result['confidence']:.3f}")
                if result['detected_issues']:
                    print(f"   Issues: {', '.join(result['detected_issues'])}")
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")

def test_batch_image_moderation():
    """Test batch image moderation."""
    print("\n" + "="*50)
    print("Testing Batch Image Moderation...")
    
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    
    # Prepare batch data
    batch_data = []
    test_images = ['safe_image.jpg', 'skin_tone_image.jpg', 'red_image.jpg']
    
    for image_name in test_images:
        image_path = os.path.join(data_dir, image_name)
        if os.path.exists(image_path):
            image_b64 = image_to_base64(image_path)
            batch_data.append({
                'id': image_name,
                'image_data': image_b64
            })
    
    if batch_data:
        try:
            api_gateway_url = "http://localhost:8000"
            response = requests.post(
                f"{api_gateway_url}/moderate/images/batch",
                json={'images': batch_data}
            )
            
            if response.status_code == 200:
                results = response.json()
                print(f"✅ Batch processing successful!")
                print(f"   Processed: {len(results['results'])} images")
                for result in results['results']:
                    print(f"   {result['id']}: {result['status']} (Safe: {result['is_safe']})")
            else:
                print(f"❌ Batch Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Batch Exception: {str(e)}")
    else:
        print("❌ No images found for batch testing")

def check_service_health():
    """Check if all services are running."""
    services = [
        ("API Gateway", "http://localhost:8000/health"),
        ("Text Service", "http://localhost:8001/health"),
        ("Image Service", "http://localhost:8002/health")
    ]
    
    print("Checking service health...")
    all_healthy = True
    
    for name, url in services:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: Healthy")
            else:
                print(f"❌ {name}: Unhealthy ({response.status_code})")
                all_healthy = False
        except Exception as e:
            print(f"❌ {name}: Not responding ({str(e)})")
            all_healthy = False
    
    return all_healthy

if __name__ == "__main__":
    print("AI Content Moderation System - Image Testing")
    print("=" * 50)
    
    # Check if services are running
    if not check_service_health():
        print("\n❌ Some services are not running. Please start all services first.")
        print("Run: python scripts/start_services.py")
        sys.exit(1)
    
    print("\n" + "="*50)
    
    # Run tests
    test_image_moderation_api()
    test_batch_image_moderation()
    
    print("\n" + "="*50)
    print("✅ Image moderation testing completed!")
