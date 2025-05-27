"""
Image Moderation API Routes
Handles API endpoints for image content moderation
"""

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import logging
import io
import sys
from pathlib import Path
from PIL import Image

# Add parent directory to Python path for imports
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from models.image_classifier import ImageModerationModel
from utils.image_preprocessor import preprocess_image, validate_image

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize the image moderation model
image_model = ImageModerationModel()

class ImageModerationResponse(BaseModel):
    is_appropriate: bool
    confidence_score: float
    flagged_categories: List[str]
    image_info: dict
    user_id: Optional[str] = None
    content_id: Optional[str] = None

@router.post("/moderate", response_model=ImageModerationResponse)
async def moderate_image(
    file: UploadFile = File(...),
    user_id: Optional[str] = None,
    content_id: Optional[str] = None
):
    """
    Moderate image content for inappropriate material
    """
    try:
        logger.info(f"Moderating image for user: {user_id}")
        
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image data
        image_data = await file.read()
        
        # Validate image
        image_info = validate_image(image_data)
        if not image_info["is_valid"]:
            raise HTTPException(status_code=400, detail=f"Invalid image: {image_info['error']}")
        
        # Preprocess image
        processed_image = preprocess_image(image_data)
        
        # Run moderation
        result = await image_model.moderate(processed_image)
        
        response = ImageModerationResponse(
            is_appropriate=result["is_appropriate"],
            confidence_score=result["confidence_score"],
            flagged_categories=result["flagged_categories"],
            image_info=image_info,
            user_id=user_id,
            content_id=content_id
        )
        
        logger.info(f"Image moderation result: {result['is_appropriate']} (confidence: {result['confidence_score']})")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during image moderation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Image moderation failed: {str(e)}")

@router.get("/categories")
async def get_moderation_categories():
    """
    Get available image moderation categories
    """
    return {
        "categories": [
            "explicit_content",
            "violence",
            "drugs",
            "weapons",
            "hate_symbols",
            "gore"
        ]
    }

@router.get("/supported-formats")
async def get_supported_formats():
    """
    Get supported image formats
    """
    return {
        "formats": ["JPEG", "PNG", "GIF", "BMP", "WEBP"],
        "max_size_mb": 10,
        "max_dimensions": "4096x4096"
    }
