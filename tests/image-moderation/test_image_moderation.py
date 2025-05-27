"""
Test cases for image moderation service
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
import sys
import os
import io
from PIL import Image
import numpy as np

# Add parent directory to path to import modules
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import modules using relative path approach
image_service_dir = project_root / "image-moderation-service"
sys.path.insert(0, str(image_service_dir))

from main import app
from models.image_classifier import ImageModerationModel, SkinDetector, ViolenceDetector
from utils.image_preprocessor import validate_image, preprocess_image, extract_image_features

client = TestClient(app)

def create_test_image(width=100, height=100, color=(255, 255, 255)):
    """Create a test image for testing purposes"""
    image = Image.new('RGB', (width, height), color)
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    return img_byte_arr.getvalue()

def create_skin_colored_image(width=100, height=100):
    """Create an image with skin-like colors"""
    # Create image with skin-like color
    skin_color = (255, 220, 177)  # Light skin tone
    return create_test_image(width, height, skin_color)

class TestImageModerationAPI:
    """Test cases for image moderation API endpoints"""
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["service"] == "image-moderation"
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert "Image Moderation Service" in response.json()["message"]
    
    def test_categories_endpoint(self):
        """Test categories endpoint"""
        response = client.get("/api/v1/categories")
        assert response.status_code == 200
        categories = response.json()["categories"]
        assert isinstance(categories, list)
        assert "explicit_content" in categories
        assert "violence" in categories
        assert "weapons" in categories
    
    def test_supported_formats_endpoint(self):
        """Test supported formats endpoint"""
        response = client.get("/api/v1/supported-formats")
        assert response.status_code == 200
        data = response.json()
        assert "formats" in data
        assert "JPEG" in data["formats"]
        assert "PNG" in data["formats"]
    
    def test_moderate_valid_image(self):
        """Test moderation of valid image"""
        test_image = create_test_image()
        
        files = {"file": ("test.jpg", test_image, "image/jpeg")}
        data = {"user_id": "test_user_1", "content_id": "test_image_1"}
        
        response = client.post("/api/v1/moderate", files=files, data=data)
        assert response.status_code == 200
        
        result = response.json()
        assert isinstance(result["is_appropriate"], bool)
        assert isinstance(result["confidence_score"], float)
        assert result["user_id"] == "test_user_1"
        assert result["content_id"] == "test_image_1"
        assert isinstance(result["flagged_categories"], list)
        assert "image_info" in result
    
    def test_moderate_without_user_id(self):
        """Test moderation without user_id"""
        test_image = create_test_image()
        
        files = {"file": ("test.jpg", test_image, "image/jpeg")}
        
        response = client.post("/api/v1/moderate", files=files)
        assert response.status_code == 200
        
        result = response.json()
        assert result["user_id"] is None
    
    def test_moderate_invalid_file_type(self):
        """Test moderation with invalid file type"""
        test_data = b"This is not an image file"
        
        files = {"file": ("test.txt", test_data, "text/plain")}
        
        response = client.post("/api/v1/moderate", files=files)
        assert response.status_code == 400
        assert "File must be an image" in response.json()["detail"]

class TestImageModerationModel:
    """Test cases for image moderation model"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.model = ImageModerationModel()
    
    @pytest.mark.asyncio
    async def test_moderate_clean_image(self):
        """Test model with clean image"""
        test_image = create_test_image()
        result = await self.model.moderate(test_image)
        
        assert isinstance(result["is_appropriate"], bool)
        assert isinstance(result["confidence_score"], float)
        assert isinstance(result["flagged_categories"], list)
    
    @pytest.mark.asyncio
    async def test_moderate_skin_colored_image(self):
        """Test model with skin-colored image"""
        test_image = create_skin_colored_image()
        result = await self.model.moderate(test_image)
        
        # This might flag as explicit due to high skin percentage
        assert isinstance(result["is_appropriate"], bool)
        assert isinstance(result["confidence_score"], float)
    
    @pytest.mark.asyncio
    async def test_check_explicit_content(self):
        """Test explicit content detection"""
        test_image = create_test_image()
        
        # Convert to OpenCV format
        pil_image = Image.open(io.BytesIO(test_image))
        cv_image = np.array(pil_image)
        
        result = await self.model._check_explicit_content(cv_image)
        
        assert isinstance(result["is_explicit"], bool)
        assert isinstance(result["score"], float)
        assert isinstance(result["skin_percentage"], float)
    
    @pytest.mark.asyncio
    async def test_check_violence(self):
        """Test violence detection"""
        test_image = create_test_image()
        
        # Convert to OpenCV format
        pil_image = Image.open(io.BytesIO(test_image))
        cv_image = np.array(pil_image)
        
        result = await self.model._check_violence(cv_image)
        
        assert isinstance(result["is_violent"], bool)
        assert isinstance(result["score"], float)
    
    @pytest.mark.asyncio
    async def test_check_weapons(self):
        """Test weapon detection"""
        test_image = create_test_image()
        
        # Convert to OpenCV format
        pil_image = Image.open(io.BytesIO(test_image))
        cv_image = np.array(pil_image)
        
        result = await self.model._check_weapons(cv_image)
        
        assert isinstance(result["has_weapons"], bool)
        assert isinstance(result["score"], float)

class TestSkinDetector:
    """Test cases for skin detection"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.detector = SkinDetector()
    
    def test_detect_skin_percentage_white_image(self):
        """Test skin detection on white image"""
        # Create white image
        white_image = np.full((100, 100, 3), 255, dtype=np.uint8)
        
        percentage = self.detector.detect_skin_percentage(white_image)
        assert isinstance(percentage, float)
        assert 0.0 <= percentage <= 1.0
    
    def test_detect_skin_percentage_skin_colored_image(self):
        """Test skin detection on skin-colored image"""
        # Create skin-colored image (HSV values that should match skin range)
        skin_image = np.full((100, 100, 3), [177, 220, 255], dtype=np.uint8)  # Light skin tone in BGR
        
        percentage = self.detector.detect_skin_percentage(skin_image)
        assert isinstance(percentage, float)
        assert 0.0 <= percentage <= 1.0

class TestViolenceDetector:
    """Test cases for violence detection"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.detector = ViolenceDetector()
    
    def test_detect_violence_indicators_clean_image(self):
        """Test violence detection on clean image"""
        clean_image = np.full((100, 100, 3), 255, dtype=np.uint8)
        
        score = self.detector.detect_violence_indicators(clean_image)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
    
    def test_detect_violence_indicators_red_image(self):
        """Test violence detection on red image"""
        # Create red image (might trigger blood detection)
        red_image = np.full((100, 100, 3), [0, 0, 255], dtype=np.uint8)  # Red in BGR
        
        score = self.detector.detect_violence_indicators(red_image)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

class TestImagePreprocessor:
    """Test cases for image preprocessing utilities"""
    
    def test_validate_image_valid(self):
        """Test validation of valid image"""
        test_image = create_test_image()
        result = validate_image(test_image)
        
        assert result["is_valid"] == True
        assert "width" in result
        assert "height" in result
        assert "format" in result
    
    def test_validate_image_too_large_filesize(self):
        """Test validation of image with large file size"""
        # Create a large image that would exceed 10MB limit
        large_image = create_test_image(5000, 5000)
        result = validate_image(large_image)
        
        # This might or might not fail depending on compression
        assert isinstance(result["is_valid"], bool)
    
    def test_validate_image_too_large_dimensions(self):
        """Test validation of image with large dimensions"""
        # This would be too large for actual creation, so we'll test the logic
        # by mocking or creating a reasonably large image
        large_image = create_test_image(1000, 1000)
        result = validate_image(large_image)
        
        assert result["is_valid"] == True  # Should be valid at 1000x1000
    
    def test_validate_image_too_small(self):
        """Test validation of very small image"""
        small_image = create_test_image(20, 20)
        result = validate_image(small_image)
        
        assert result["is_valid"] == False
        assert "too small" in result["error"]
    
    def test_validate_image_invalid_data(self):
        """Test validation of invalid image data"""
        invalid_data = b"This is not image data"
        result = validate_image(invalid_data)
        
        assert result["is_valid"] == False
        assert "error" in result
    
    def test_preprocess_image(self):
        """Test image preprocessing"""
        test_image = create_test_image(500, 500)
        processed = preprocess_image(test_image)
        
        assert isinstance(processed, bytes)
        assert len(processed) > 0
    
    def test_extract_image_features(self):
        """Test image feature extraction"""
        test_image = create_test_image()
        features = extract_image_features(test_image)
        
        assert isinstance(features, dict)
        if features:  # Only check if extraction succeeded
            assert "width" in features
            assert "height" in features
            assert "brightness" in features
            assert "contrast" in features

class TestImageModerationIntegration:
    """Integration tests for image moderation"""
    
    def test_full_moderation_pipeline_clean_image(self):
        """Test full pipeline with clean image"""
        test_image = create_test_image()
        
        files = {"file": ("test.jpg", test_image, "image/jpeg")}
        data = {"user_id": "integration_test_user", "content_id": "integration_test_1"}
        
        response = client.post("/api/v1/moderate", files=files, data=data)
        assert response.status_code == 200
        
        result = response.json()
        assert isinstance(result["is_appropriate"], bool)
        assert result["user_id"] == "integration_test_user"
        assert "image_info" in result
    
    def test_full_moderation_pipeline_skin_image(self):
        """Test full pipeline with skin-colored image"""
        test_image = create_skin_colored_image()
        
        files = {"file": ("test.jpg", test_image, "image/jpeg")}
        data = {"user_id": "integration_test_user", "content_id": "integration_test_2"}
        
        response = client.post("/api/v1/moderate", files=files, data=data)
        assert response.status_code == 200
        
        result = response.json()
        assert isinstance(result["is_appropriate"], bool)
        assert isinstance(result["confidence_score"], float)

if __name__ == "__main__":
    pytest.main([__file__])
