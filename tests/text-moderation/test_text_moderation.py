"""
Test cases for text moderation service
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path to import modules
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import modules using relative path approach
text_service_dir = project_root / "text-moderation-service"
sys.path.insert(0, str(text_service_dir))

from main import app
from models.text_classifier import TextModerationModel
from utils.text_preprocessor import preprocess_text, handle_character_substitutions

client = TestClient(app)

class TestTextModerationAPI:
    """Test cases for text moderation API endpoints"""
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["service"] == "text-moderation"
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert "Text Moderation Service" in response.json()["message"]
    
    def test_categories_endpoint(self):
        """Test categories endpoint"""
        response = client.get("/api/v1/categories")
        assert response.status_code == 200
        categories = response.json()["categories"]
        assert isinstance(categories, list)
        assert "hate_speech" in categories
        assert "profanity" in categories
    
    def test_moderate_clean_text(self):
        """Test moderation of clean text"""
        request_data = {
            "text": "This is a perfectly normal and appropriate message.",
            "user_id": "test_user_1",
            "content_id": "test_content_1"
        }
        
        response = client.post("/api/v1/moderate", json=request_data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["is_appropriate"] == True
        assert result["confidence_score"] >= 0.0
        assert result["user_id"] == "test_user_1"
        assert result["content_id"] == "test_content_1"
        assert isinstance(result["flagged_categories"], list)
    
    def test_moderate_profane_text(self):
        """Test moderation of text with profanity"""
        request_data = {
            "text": "This is a damn stupid message with shit content.",
            "user_id": "test_user_2"
        }
        
        response = client.post("/api/v1/moderate", json=request_data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["is_appropriate"] == False
        assert result["confidence_score"] > 0.0
        assert "profanity" in result["flagged_categories"]
    
    def test_moderate_empty_text(self):
        """Test moderation of empty text"""
        request_data = {
            "text": "",
            "user_id": "test_user_3"
        }
        
        response = client.post("/api/v1/moderate", json=request_data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["is_appropriate"] == True
        assert result["confidence_score"] == 0.0
    
    def test_moderate_without_user_id(self):
        """Test moderation without user_id"""
        request_data = {
            "text": "Test message without user ID"
        }
        
        response = client.post("/api/v1/moderate", json=request_data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["user_id"] is None

class TestTextModerationModel:
    """Test cases for text moderation model"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.model = TextModerationModel()
    
    @pytest.mark.asyncio
    async def test_moderate_clean_text(self):
        """Test model with clean text"""
        result = await self.model.moderate("This is a clean message.")
        
        assert result["is_appropriate"] == True
        assert result["confidence_score"] >= 0.0
        assert len(result["flagged_categories"]) == 0
    
    @pytest.mark.asyncio
    async def test_moderate_profane_text(self):
        """Test model with profane text"""
        result = await self.model.moderate("This is fucking bullshit!")
        
        assert result["is_appropriate"] == False
        assert result["confidence_score"] > 0.0
        assert "profanity" in result["flagged_categories"]
    
    def test_check_profanity(self):
        """Test profanity detection"""
        score = self.model._check_profanity("This is damn good shit!")
        assert score > 0.0
        
        score = self.model._check_profanity("This is perfectly clean.")
        assert score == 0.0
    
    @pytest.mark.asyncio
    async def test_check_toxicity(self):
        """Test toxicity detection"""
        result = await self.model._check_toxicity("You are an idiot and should die!")
        assert isinstance(result["is_toxic"], bool)
        assert isinstance(result["score"], float)
        assert isinstance(result["categories"], list)

class TestTextPreprocessor:
    """Test cases for text preprocessing utilities"""
    
    def test_preprocess_text_basic(self):
        """Test basic text preprocessing"""
        original = "  This IS   a TEST message!  "
        processed = preprocess_text(original)
        
        assert processed == "this is a test message!"
    
    def test_preprocess_text_with_urls(self):
        """Test preprocessing with URLs"""
        original = "Check this out: https://example.com/test"
        processed = preprocess_text(original)
        
        assert "[URL]" in processed
        assert "https://example.com/test" not in processed
    
    def test_preprocess_text_with_emails(self):
        """Test preprocessing with email addresses"""
        original = "Contact me at test@example.com for details"
        processed = preprocess_text(original)
        
        assert "[EMAIL]" in processed
        assert "test@example.com" not in processed
    
    def test_handle_character_substitutions(self):
        """Test character substitution handling"""
        original = "h3ll0 w0rld! th1s 1s @ t3st"
        processed = handle_character_substitutions(original)
        
        assert "hello world! this is a test" == processed
    
    def test_preprocess_empty_text(self):
        """Test preprocessing empty text"""
        assert preprocess_text("") == ""
        assert preprocess_text(None) == ""

class TestTextModerationIntegration:
    """Integration tests for text moderation"""
    
    def test_full_moderation_pipeline_clean(self):
        """Test full pipeline with clean text"""
        request_data = {
            "text": "Hello, how are you doing today? I hope you're having a great day!",
            "user_id": "integration_test_user",
            "content_id": "integration_test_1"
        }
        
        response = client.post("/api/v1/moderate", json=request_data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["is_appropriate"] == True
        assert len(result["processed_text"]) > 0
        assert result["user_id"] == "integration_test_user"
    
    def test_full_moderation_pipeline_inappropriate(self):
        """Test full pipeline with inappropriate text"""
        request_data = {
            "text": "You f*cking piece of sh*t, I hate you so much!",
            "user_id": "integration_test_user",
            "content_id": "integration_test_2"
        }
        
        response = client.post("/api/v1/moderate", json=request_data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["is_appropriate"] == False
        assert result["confidence_score"] > 0.0
        assert len(result["flagged_categories"]) > 0

if __name__ == "__main__":
    pytest.main([__file__])
