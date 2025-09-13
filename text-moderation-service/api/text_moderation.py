"""
Text Moderation API Routes
Handles API endpoints for text content moderation
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional, List
import logging
import sys
from pathlib import Path

# Add parent directory to Python path for imports
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

# Try to import Rust-based classifier first, fallback to original
try:
    from models.rust_text_classifier import RustTextModerationModel
    text_model = RustTextModerationModel()
    logger = logging.getLogger(__name__)
    logger.info("Using Rust-based text moderation model")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Rust model not available: {e}. Falling back to original model.")
    try:
        from models.text_classifier import TextModerationModel
        text_model = TextModerationModel()
        logger.info("Using original Python text moderation model")
    except ImportError as e2:
        logger.error(f"No text moderation model available: {e2}")
        text_model = None

from utils.text_preprocessor import preprocess_text

router = APIRouter()

class TextModerationRequest(BaseModel):
    text: str
    user_id: Optional[str] = None
    content_id: Optional[str] = None

class BatchTextModerationRequest(BaseModel):
    texts: List[str]
    user_id: Optional[str] = None

class TextModerationResponse(BaseModel):
    is_appropriate: bool
    confidence_score: float
    flagged_categories: list
    processed_text: str
    user_id: Optional[str] = None
    content_id: Optional[str] = None

class BatchTextModerationResponse(BaseModel):
    results: List[TextModerationResponse]
    user_id: Optional[str] = None

@router.post("/moderate", response_model=TextModerationResponse)
async def moderate_text(request: TextModerationRequest):
    """
    Moderate text content for inappropriate material
    """
    if text_model is None:
        raise HTTPException(status_code=503, detail="Text moderation service unavailable")
    
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
            processed_text=result.get("processed_text", processed_text),
            user_id=request.user_id,
            content_id=request.content_id
        )
        
        logger.info(f"Moderation result: {result['is_appropriate']} (confidence: {result['confidence_score']})")
        return response
        
    except Exception as e:
        logger.error(f"Error during text moderation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Text moderation failed: {str(e)}")

@router.post("/moderate/batch", response_model=BatchTextModerationResponse)
async def moderate_text_batch(request: BatchTextModerationRequest):
    """
    Moderate multiple texts in batch for better performance
    """
    if text_model is None:
        raise HTTPException(status_code=503, detail="Text moderation service unavailable")
    
    try:
        logger.info(f"Batch moderating {len(request.texts)} texts for user: {request.user_id}")
        
        # Preprocess all texts
        processed_texts = [preprocess_text(text) for text in request.texts]
        
        # Run batch moderation if available
        if hasattr(text_model, 'moderate_batch'):
            results = await text_model.moderate_batch(processed_texts)
        else:
            # Fallback to individual moderation
            results = []
            for processed_text in processed_texts:
                result = await text_model.moderate(processed_text)
                results.append(result)
        
        responses = []
        for i, result in enumerate(results):
            response = TextModerationResponse(
                is_appropriate=result["is_appropriate"],
                confidence_score=result["confidence_score"],
                flagged_categories=result["flagged_categories"],
                processed_text=result.get("processed_text", processed_texts[i]),
                user_id=request.user_id,
                content_id=f"batch_{i}"
            )
            responses.append(response)
        
        logger.info(f"Batch moderation completed. {len(responses)} results")
        return BatchTextModerationResponse(
            results=responses,
            user_id=request.user_id
        )
        
    except Exception as e:
        logger.error(f"Error during batch text moderation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch text moderation failed: {str(e)}")

@router.get("/categories")
async def get_moderation_categories():
    """
    Get available moderation categories
    """
    return {
        "categories": [
            "profanity",
            "threats", 
            "spam",
            "excessive_caps",
            "spam_chars",
            "hate_speech",
            "toxic",
            "sexual_content"
        ]
    }

@router.get("/backend-info")
async def get_backend_info():
    """
    Get information about the moderation backend
    """
    if text_model is None:
        return {"error": "No text moderation model available"}
    
    if hasattr(text_model, 'get_backend_info'):
        return text_model.get_backend_info()
    else:
        return {
            "rust_available": False,
            "backend": "Python (Legacy)",
            "features": ["basic_moderation"]
        }

@router.get("/health")
async def health_check():
    """
    Health check for text moderation service
    """
    if text_model is None:
        raise HTTPException(status_code=503, detail="Text moderation model not available")
    
    is_rust = hasattr(text_model, 'is_rust_available') and text_model.is_rust_available()
    
    return {
        "status": "healthy",
        "service": "text-moderation",
        "backend": "rust" if is_rust else "python",
        "features": ["single_moderation", "batch_moderation", "categories"]
    }
