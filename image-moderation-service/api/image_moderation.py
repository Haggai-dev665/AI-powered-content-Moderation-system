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

# Try to import Rust-enhanced classifier first, fallback to original
try:
    from models.rust_image_classifier import RustImageModerationModel
    image_model = RustImageModerationModel()
    logger = logging.getLogger(__name__)
    logger.info("Using Rust-enhanced image moderation model")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Rust image model not available: {e}. Falling back to original model.")
    try:
        from models.image_classifier import ImageModerationModel
        image_model = ImageModerationModel()
        logger.info("Using original Python image moderation model")
    except ImportError as e2:
        logger.error(f"No image moderation model available: {e2}")
        image_model = None

from utils.image_preprocessor import preprocess_image

router = APIRouter()

class ImageModerationResponse(BaseModel):
    is_appropriate: bool
    confidence_score: float
    flagged_categories: List[str]
    image_info: dict
    user_id: Optional[str] = None
    content_id: Optional[str] = None

class ImageValidationResponse(BaseModel):
    is_valid: bool
    image_info: dict
    error: Optional[str] = None

@router.post("/moderate", response_model=ImageModerationResponse)
async def moderate_image(
    file: UploadFile = File(...),
    user_id: Optional[str] = None,
    content_id: Optional[str] = None
):
    """
    Moderate image content for inappropriate material
    """
    if image_model is None:
        raise HTTPException(status_code=503, detail="Image moderation service unavailable")
    
    try:
        logger.info(f"Moderating image '{file.filename}' for user: {user_id}")
        
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image data
        image_data = await file.read()
        
        # Check file size
        if len(image_data) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")
        
        # Run moderation (includes validation)
        result = await image_model.moderate(image_data, file.filename)
        
        # Handle validation errors
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        response = ImageModerationResponse(
            is_appropriate=result["is_appropriate"],
            confidence_score=result["confidence_score"],
            flagged_categories=result["flagged_categories"],
            image_info=result.get("image_info", {}),
            user_id=user_id,
            content_id=content_id
        )
        
        logger.info(f"Image moderation result: {result['is_appropriate']} (confidence: {result['confidence_score']}) - {result['flagged_categories']}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during image moderation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Image moderation failed: {str(e)}")

@router.post("/validate", response_model=ImageValidationResponse)
async def validate_image_endpoint(file: UploadFile = File(...)):
    """
    Validate image without moderation
    """
    if image_model is None:
        raise HTTPException(status_code=503, detail="Image moderation service unavailable")
    
    try:
        logger.info(f"Validating image '{file.filename}'")
        
        # Read image data
        image_data = await file.read()
        
        # Run validation
        validation = await image_model.validate_image(image_data, file.filename)
        
        response = ImageValidationResponse(
            is_valid=validation["is_valid"],
            image_info=validation,
            error=validation.get("error")
        )
        
        logger.info(f"Image validation result: {validation['is_valid']}")
        return response
        
    except Exception as e:
        logger.error(f"Error during image validation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Image validation failed: {str(e)}")

@router.get("/categories")
async def get_moderation_categories():
    """
    Get available image moderation categories
    """
    return {
        "categories": [
            "explicit_content",
            "violence",
            "weapons",
            "inappropriate_text",
            "suspicious_dimensions",
            "invalid_image",
            "drugs",
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
        "formats": ["JPEG", "JPG", "PNG", "GIF", "BMP", "WEBP"],
        "max_size_mb": 10,
        "max_dimensions": "No specific limit",
        "extensions": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]
    }

@router.get("/backend-info")
async def get_backend_info():
    """
    Get information about the image moderation backend
    """
    if image_model is None:
        return {"error": "No image moderation model available"}
    
    if hasattr(image_model, 'get_backend_info'):
        return image_model.get_backend_info()
    else:
        return {
            "rust_available": False,
            "backend": "Python (Legacy)",
            "features": ["basic_moderation"]
        }

@router.get("/health")
async def health_check():
    """
    Health check for image moderation service
    """
    if image_model is None:
        raise HTTPException(status_code=503, detail="Image moderation model not available")
    
    is_rust = hasattr(image_model, 'is_rust_available') and image_model.is_rust_available()
    
    return {
        "status": "healthy",
        "service": "image-moderation",
        "backend": "rust+python" if is_rust else "python",
        "features": ["image_validation", "moderation", "format_support"]
    }
