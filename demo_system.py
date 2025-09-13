#!/usr/bin/env python3
"""
Comprehensive Demo and Test Script for AI-Powered Content Moderation System
Tests both text and image moderation with Rust backend integration
"""

import requests
import json
import time
import sys
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np

class ContentModerationDemo:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.text_service_url = "http://localhost:8001"
        self.image_service_url = "http://localhost:8002"
        
        # Create demo images
        self.create_demo_images()
    
    def create_demo_images(self):
        """Create demo images for testing"""
        demo_dir = Path("demo_images")
        demo_dir.mkdir(exist_ok=True)
        
        # Create a clean test image
        clean_img = Image.new('RGB', (300, 200), color='lightblue')
        draw = ImageDraw.Draw(clean_img)
        draw.text((50, 50), "Clean Content", fill='black')
        clean_img.save(demo_dir / "clean_image.png")
        
        # Create an image with lots of skin tone colors (potentially flagged)
        skin_img = Image.new('RGB', (300, 200), color=(220, 180, 140))  # Skin tone
        skin_img.save(demo_dir / "skin_tone_image.png")
        
        # Create an image with red colors (potentially flagged as violence)
        red_img = Image.new('RGB', (300, 200), color='red')
        draw = ImageDraw.Draw(red_img)
        draw.text((50, 50), "Red Alert", fill='white')
        red_img.save(demo_dir / "red_image.png")
        
        # Create a very small image (tracking pixel test)
        tiny_img = Image.new('RGB', (1, 1), color='black')
        tiny_img.save(demo_dir / "tiny_image.png")
        
        print(f"✓ Demo images created in {demo_dir}/")
        return demo_dir
    
    def test_service_health(self):
        """Test all service health endpoints"""
        print("\n🏥 Testing Service Health...")
        
        services = [
            ("API Gateway", f"{self.base_url}/health"),
            ("Text Service", f"{self.text_service_url}/health"),
            ("Image Service", f"{self.image_service_url}/health"),
        ]
        
        for name, url in services:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    print(f"  ✓ {name}: {data.get('status', 'unknown')}")
                else:
                    print(f"  ✗ {name}: HTTP {response.status_code}")
            except requests.RequestException as e:
                print(f"  ✗ {name}: {str(e)}")
    
    def test_backend_info(self):
        """Test backend information endpoints"""
        print("\n🔧 Backend Information...")
        
        # Text service backend
        try:
            response = requests.get(f"{self.text_service_url}/api/v1/backend-info")
            if response.status_code == 200:
                data = response.json()
                print(f"  Text Service: {data.get('backend', 'unknown')} (Rust: {data.get('rust_available', False)})")
            else:
                print(f"  Text Service: Error {response.status_code}")
        except requests.RequestException as e:
            print(f"  Text Service: {str(e)}")
        
        # Image service backend
        try:
            response = requests.get(f"{self.image_service_url}/api/v1/backend-info")
            if response.status_code == 200:
                data = response.json()
                print(f"  Image Service: {data.get('backend', 'unknown')} (Rust: {data.get('rust_available', False)})")
            else:
                print(f"  Image Service: Error {response.status_code}")
        except requests.RequestException as e:
            print(f"  Image Service: {str(e)}")
    
    def test_text_moderation(self):
        """Test text moderation with various examples"""
        print("\n📝 Testing Text Moderation...")
        
        test_texts = [
            ("Clean text", "This is a perfectly normal and appropriate message."),
            ("Profanity", "This fucking message has bad words in it."),
            ("Threats", "I will kill you if you don't listen."),
            ("Spam", "Click here to buy viagra now! Free money!"),
            ("Excessive caps", "THIS IS SHOUTING WITH EXCESSIVE CAPS!!!"),
            ("Repeated chars", "Hellooooooooo world!"),
            ("Mixed issues", "FUCK this spammy site www.badsite.com"),
        ]
        
        for description, text in test_texts:
            try:
                response = requests.post(
                    f"{self.base_url}/api/v1/moderate/text",
                    json={
                        "text": text,
                        "user_id": "demo_user",
                        "content_id": f"demo_{description.lower().replace(' ', '_')}"
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = "✓ PASS" if data["is_appropriate"] else "✗ FLAGGED"
                    categories = ", ".join(data["flagged_categories"]) if data["flagged_categories"] else "None"
                    print(f"  {status} {description}: {categories} (confidence: {data['confidence_score']:.2f})")
                else:
                    print(f"  ✗ {description}: HTTP {response.status_code}")
                    
            except requests.RequestException as e:
                print(f"  ✗ {description}: {str(e)}")
    
    def test_batch_text_moderation(self):
        """Test batch text moderation"""
        print("\n📦 Testing Batch Text Moderation...")
        
        texts = [
            "Clean message one",
            "Another clean message",
            "This fucking bad message",
            "I will murder you",
            "EXCESSIVE CAPS MESSAGE"
        ]
        
        try:
            response = requests.post(
                f"{self.text_service_url}/api/v1/moderate/batch",
                json={
                    "texts": texts,
                    "user_id": "demo_user"
                },
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"  ✓ Processed {len(data['results'])} texts in batch")
                for i, result in enumerate(data['results']):
                    status = "PASS" if result["is_appropriate"] else "FLAGGED"
                    categories = ", ".join(result["flagged_categories"]) if result["flagged_categories"] else "None"
                    print(f"    {i+1}. {status}: {categories}")
            else:
                print(f"  ✗ Batch processing failed: HTTP {response.status_code}")
                
        except requests.RequestException as e:
            print(f"  ✗ Batch processing error: {str(e)}")
    
    def test_image_moderation(self):
        """Test image moderation with demo images"""
        print("\n🖼️  Testing Image Moderation...")
        
        demo_dir = Path("demo_images")
        test_images = [
            ("clean_image.png", "Clean content"),
            ("skin_tone_image.png", "Skin tone colors"),
            ("red_image.png", "Red colors"),
            ("tiny_image.png", "Tracking pixel size"),
        ]
        
        for filename, description in test_images:
            image_path = demo_dir / filename
            if not image_path.exists():
                print(f"  ✗ {description}: Image {filename} not found")
                continue
            
            try:
                with open(image_path, 'rb') as f:
                    files = {'file': (filename, f, 'image/png')}
                    data = {
                        'user_id': 'demo_user',
                        'content_id': f'demo_{filename}'
                    }
                    
                    response = requests.post(
                        f"{self.base_url}/api/v1/moderate/image",
                        files=files,
                        data=data,
                        timeout=15
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    status = "✓ PASS" if result["is_appropriate"] else "✗ FLAGGED"
                    categories = ", ".join(result["flagged_categories"]) if result["flagged_categories"] else "None"
                    image_info = result.get("image_info", {})
                    size_info = f"{image_info.get('width', '?')}x{image_info.get('height', '?')}"
                    print(f"  {status} {description} ({size_info}): {categories} (confidence: {result['confidence_score']:.2f})")
                else:
                    print(f"  ✗ {description}: HTTP {response.status_code} - {response.text}")
                    
            except requests.RequestException as e:
                print(f"  ✗ {description}: {str(e)}")
    
    def test_image_validation(self):
        """Test image validation endpoint"""
        print("\n🔍 Testing Image Validation...")
        
        demo_dir = Path("demo_images")
        test_images = ["clean_image.png", "tiny_image.png"]
        
        for filename in test_images:
            image_path = demo_dir / filename
            if not image_path.exists():
                continue
            
            try:
                with open(image_path, 'rb') as f:
                    files = {'file': (filename, f, 'image/png')}
                    
                    response = requests.post(
                        f"{self.image_service_url}/api/v1/validate",
                        files=files,
                        timeout=10
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    status = "✓ VALID" if result["is_valid"] else "✗ INVALID"
                    info = result.get("image_info", {})
                    size = f"{info.get('width', '?')}x{info.get('height', '?')}"
                    format_info = info.get('format', '?')
                    print(f"  {status} {filename}: {size} {format_info}")
                else:
                    print(f"  ✗ {filename}: HTTP {response.status_code}")
                    
            except requests.RequestException as e:
                print(f"  ✗ {filename}: {str(e)}")
    
    def performance_test(self):
        """Run basic performance tests"""
        print("\n⚡ Performance Testing...")
        
        # Text performance test
        test_text = "This is a sample text for performance testing."
        start_time = time.time()
        
        for i in range(10):
            try:
                response = requests.post(
                    f"{self.text_service_url}/api/v1/moderate",
                    json={"text": test_text, "user_id": "perf_test"},
                    timeout=5
                )
            except:
                pass
        
        text_time = (time.time() - start_time) / 10
        print(f"  Text moderation: {text_time:.3f}s per request")
        
        # Batch performance test
        texts = [test_text] * 10
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.text_service_url}/api/v1/moderate/batch",
                json={"texts": texts, "user_id": "perf_test"},
                timeout=10
            )
            batch_time = time.time() - start_time
            print(f"  Batch text moderation: {batch_time:.3f}s for 10 items ({batch_time/10:.3f}s per item)")
        except:
            print("  Batch text moderation: Failed")
    
    def run_demo(self):
        """Run the complete demo"""
        print("=" * 60)
        print("🚀 AI-Powered Content Moderation System Demo")
        print("=" * 60)
        
        self.test_service_health()
        self.test_backend_info()
        self.test_text_moderation()
        self.test_batch_text_moderation()
        self.test_image_validation()
        self.test_image_moderation()
        self.performance_test()
        
        print("\n" + "=" * 60)
        print("✅ Demo completed!")
        print("=" * 60)
        print("\n📊 Summary:")
        print("- Rust-powered text moderation with offline detection")
        print("- Enhanced image moderation with validation")
        print("- Batch processing for high throughput")
        print("- Comprehensive API with health monitoring")
        print("- Production-ready content filtering")

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        demo = ContentModerationDemo()
        demo.test_service_health()
        demo.test_backend_info()
        print("\n✅ Quick health check completed!")
    else:
        demo = ContentModerationDemo()
        demo.run_demo()

if __name__ == "__main__":
    main()