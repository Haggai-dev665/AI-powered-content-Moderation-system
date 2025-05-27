"""
Demo script for AI Content Moderation System
Demonstrates the capabilities of the system with sample content
"""

import requests
import time
import logging
import base64
from pathlib import Path
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModerationDemo:
    """Demo class for content moderation system"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.timeout = 30
    
    def test_text_moderation(self):
        """Demonstrate text moderation capabilities"""
        logger.info("🔤 Demonstrating Text Moderation")
        logger.info("-" * 40)
        
        test_texts = [
            {
                "text": "Hello, this is a normal and friendly message!",
                "description": "Clean text"
            },
            {
                "text": "You are stupid and I hate you!",
                "description": "Toxic content"
            },
            {
                "text": "This product is amazing, I love it so much!",
                "description": "Positive sentiment"
            },
            {
                "text": "damn this is a great product",
                "description": "Mild profanity"
            },
            {
                "text": "I think we should have a respectful discussion about this topic.",
                "description": "Constructive text"
            }
        ]
        
        for i, test_case in enumerate(test_texts, 1):
            logger.info(f"\nTest {i}: {test_case['description']}")
            logger.info(f"Input: \"{test_case['text']}\"")
            
            try:
                response = requests.post(
                    f"{self.base_url}/text/moderate",
                    json={"text": test_case["text"]},
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Result: {result['action']}")
                    logger.info(f"Toxicity Score: {result['scores']['toxicity']:.3f}")
                    logger.info(f"Hate Speech Score: {result['scores']['hate_speech']:.3f}")
                    
                    if result['issues']:
                        logger.info(f"Issues Found: {', '.join(result['issues'])}")
                    else:
                        logger.info("No issues detected")
                        
                else:
                    logger.error(f"Request failed: HTTP {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Error: {e}")
    
    def test_batch_text_moderation(self):
        """Demonstrate batch text moderation"""
        logger.info("\n📦 Demonstrating Batch Text Moderation")
        logger.info("-" * 40)
        
        batch_texts = [
            "This is a great product!",
            "I hate this stupid thing",
            "Amazing quality and fast delivery",
            "This is terrible, worst purchase ever"
        ]
        
        logger.info(f"Processing {len(batch_texts)} texts in batch...")
        
        try:
            response = requests.post(
                f"{self.base_url}/text/moderate/batch",
                json={"texts": batch_texts},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                results = response.json()
                
                for i, (text, result) in enumerate(zip(batch_texts, results["results"]), 1):
                    logger.info(f"\nBatch Item {i}:")
                    logger.info(f"Text: \"{text}\"")
                    logger.info(f"Action: {result['action']}")
                    logger.info(f"Toxicity: {result['scores']['toxicity']:.3f}")
                    
            else:
                logger.error(f"Batch request failed: HTTP {response.status_code}")
                
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
    
    def create_sample_image(self) -> bytes:
        """Create a simple test image"""
        try:
            from PIL import Image, ImageDraw
            import io
            
            # Create a simple image
            img = Image.new('RGB', (200, 100), color='lightblue')
            draw = ImageDraw.Draw(img)
            draw.text((10, 40), "Test Image", fill='black')
            
            # Convert to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            return img_bytes.getvalue()
            
        except ImportError:
            logger.warning("PIL not available, skipping image creation")
            return None
    
    def test_image_moderation(self):
        """Demonstrate image moderation capabilities"""
        logger.info("\n🖼️  Demonstrating Image Moderation")
        logger.info("-" * 40)
        
        # Create a sample image
        image_data = self.create_sample_image()
        
        if image_data is None:
            logger.warning("Skipping image moderation demo (PIL not available)")
            return
        
        logger.info("Testing with a sample image...")
        
        try:
            # Encode image as base64
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            response = requests.post(
                f"{self.base_url}/image/moderate",
                json={"image": image_b64},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Result: {result['action']}")
                logger.info(f"Explicit Content Score: {result['scores']['explicit_content']:.3f}")
                logger.info(f"Violence Score: {result['scores']['violence']:.3f}")
                logger.info(f"Weapons Score: {result['scores']['weapons']:.3f}")
                
                if result['issues']:
                    logger.info(f"Issues Found: {', '.join(result['issues'])}")
                else:
                    logger.info("No issues detected")
                    
            else:
                logger.error(f"Image moderation failed: HTTP {response.status_code}")
                
        except Exception as e:
            logger.error(f"Image moderation error: {e}")
    
    def test_system_status(self):
        """Check system status and metrics"""
        logger.info("\n📊 System Status and Metrics")
        logger.info("-" * 40)
        
        try:
            # Check gateway status
            response = requests.get(f"{self.base_url}/status", timeout=self.timeout)
            
            if response.status_code == 200:
                status = response.json()
                logger.info("System Status:")
                logger.info(f"  Gateway: {status['gateway']['status']}")
                logger.info(f"  Text Service: {status['text_service']['status']}")
                logger.info(f"  Image Service: {status['image_service']['status']}")
                logger.info(f"  Total Requests: {status['stats']['total_requests']}")
                
            else:
                logger.error(f"Status check failed: HTTP {response.status_code}")
                
        except Exception as e:
            logger.error(f"Status check error: {e}")
    
    def run_full_demo(self):
        """Run the complete demonstration"""
        logger.info("🚀 AI Content Moderation System Demo")
        logger.info("=" * 50)
        
        # Check if system is running
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code != 200:
                logger.error("System not responding. Please ensure services are running.")
                return
        except Exception:
            logger.error("Cannot connect to system. Please ensure services are running.")
            logger.info("Start services with: python scripts/start_services.py")
            return
        
        # Run demonstrations
        self.test_text_moderation()
        self.test_batch_text_moderation()
        self.test_image_moderation()
        self.test_system_status()
        
        logger.info("\n" + "=" * 50)
        logger.info("🎉 Demo completed successfully!")
        logger.info("Visit http://localhost:8000/docs for interactive API documentation")

def main():
    """Main function"""
    demo = ModerationDemo()
    demo.run_full_demo()

if __name__ == "__main__":
    main()
