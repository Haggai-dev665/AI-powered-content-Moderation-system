"""
Text Moderation API Routes
Handles API endpoints for text content moderation
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
import logging
import sys
from pathlib import Path

# Add parent directory to Python path for imports
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from models.text_classifier import TextModerationModel
from utils.text_preprocessor import preprocess_text

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize the text moderation model
text_model = TextModerationModel()

class TextModerationRequest(BaseModel):
    text: str
    user_id: Optional[str] = None
    content_id: Optional[str] = None

class TextModerationResponse(BaseModel):
    is_appropriate: bool
    confidence_score: float
    flagged_categories: list
    processed_text: str
    user_id: Optional[str] = None
    content_id: Optional[str] = None

@router.post("/moderate", response_model=TextModerationResponse)
async def moderate_text(request: TextModerationRequest):
    """
    Moderate text content for inappropriate material
    """
    try:
        logger.info(f"Moderating text for user: {request.user_id}")
        
        # Preprocess the text
        processed_text = preprocess_text(request.text)
        
        # Run moderation
        result = await text_model.moderate(processed_text)
        
        response = TextModerationResponse(
            is_appropriate=result["is_appropriate"],
            confidence_score=result["confidence_score"],
            flagged_categories=result["flagged_categories"],
            processed_text=processed_text,
            user_id=request.user_id,
            content_id=request.content_id
        )
        
        logger.info(f"Moderation result: {result['is_appropriate']} (confidence: {result['confidence_score']})")
        return response
        
    except Exception as e:
        logger.error(f"Error during text moderation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Text moderation failed: {str(e)}")

@router.get("/categories")
async def get_moderation_categories():
    """
    Get available moderation categories
    """
    return {
        "categories": [
            "hate_speech",
            "profanity",
            "toxic",
            "threat",
            "sexual_content",
            "spam"
        ]
    }
