"""
Gateway Routes
Handles routing requests to appropriate microservices
"""

from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from pydantic import BaseModel
from typing import Optional
import httpx
import logging
import os
import json

logger = logging.getLogger(__name__)
router = APIRouter()

# Service URLs
TEXT_SERVICE_URL = os.getenv("TEXT_SERVICE_URL", "http://localhost:8001")
IMAGE_SERVICE_URL = os.getenv("IMAGE_SERVICE_URL", "http://localhost:8002")

class TextModerationRequest(BaseModel):
    text: str
    user_id: Optional[str] = None
    content_id: Optional[str] = None

class BatchTextModerationRequest(BaseModel):
    texts: list[str]
    user_id: Optional[str] = None

@router.post("/moderate/text")
async def moderate_text(request: TextModerationRequest):
    """
    Route text moderation requests to text moderation service
    """
    try:
        logger.info(f"Routing text moderation request for user: {request.user_id}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{TEXT_SERVICE_URL}/api/v1/moderate",
                json=request.dict(),
                timeout=30.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Text service error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Text moderation service error: {response.text}"
                )
                
    except httpx.TimeoutException:
        logger.error("Text moderation service timeout")
        raise HTTPException(status_code=504, detail="Text moderation service timeout")
    except httpx.ConnectError:
        logger.error("Cannot connect to text moderation service")
        raise HTTPException(status_code=503, detail="Text moderation service unavailable")
    except Exception as e:
        logger.error(f"Gateway error during text moderation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Gateway error: {str(e)}")

@router.post("/moderate/text/batch")
async def moderate_text_batch(request: BatchTextModerationRequest):
    """
    Route batch text moderation requests
    """
    try:
        logger.info(f"Routing batch text moderation for {len(request.texts)} texts")
        
        results = []
        async with httpx.AsyncClient() as client:
            for i, text in enumerate(request.texts):
                text_request = TextModerationRequest(
                    text=text,
                    user_id=request.user_id,
                    content_id=f"batch_{i}"
                )
                
                response = await client.post(
                    f"{TEXT_SERVICE_URL}/api/v1/moderate",
                    json=text_request.dict(),
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    result["batch_index"] = i
                    results.append(result)
                else:
                    results.append({
                        "batch_index": i,
                        "error": f"Service error: {response.status_code}",
                        "is_appropriate": False,
                        "confidence_score": 0.0,
                        "flagged_categories": ["error"]
                    })
        
        return {
            "results": results,
            "total_processed": len(results),
            "user_id": request.user_id
        }
        
    except Exception as e:
        logger.error(f"Gateway error during batch text moderation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch moderation error: {str(e)}")

@router.post("/moderate/image")
async def moderate_image(
    file: UploadFile = File(...),
    user_id: Optional[str] = Form(None),
    content_id: Optional[str] = Form(None)
):
    """
    Route image moderation requests to image moderation service
    """
    try:
        logger.info(f"Routing image moderation request for user: {user_id}")
        
        # Prepare form data for the image service
        files = {"file": (file.filename, await file.read(), file.content_type)}
        data = {}
        if user_id:
            data["user_id"] = user_id
        if content_id:
            data["content_id"] = content_id
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{IMAGE_SERVICE_URL}/api/v1/moderate",
                files=files,
                data=data,
                timeout=60.0  # Longer timeout for image processing
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Image service error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Image moderation service error: {response.text}"
                )
                
    except httpx.TimeoutException:
        logger.error("Image moderation service timeout")
        raise HTTPException(status_code=504, detail="Image moderation service timeout")
    except httpx.ConnectError:
        logger.error("Cannot connect to image moderation service")
        raise HTTPException(status_code=503, detail="Image moderation service unavailable")
    except Exception as e:
        logger.error(f"Gateway error during image moderation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Gateway error: {str(e)}")

@router.get("/moderate/categories")
async def get_all_categories():
    """
    Get all available moderation categories from both services
    """
    try:
        categories = {
            "text": [],
            "image": []
        }
        
        async with httpx.AsyncClient() as client:
            # Get text categories
            try:
                response = await client.get(f"{TEXT_SERVICE_URL}/api/v1/categories", timeout=10.0)
                if response.status_code == 200:
                    categories["text"] = response.json().get("categories", [])
            except Exception as e:
                logger.warning(f"Could not fetch text categories: {str(e)}")
            
            # Get image categories
            try:
                response = await client.get(f"{IMAGE_SERVICE_URL}/api/v1/categories", timeout=10.0)
                if response.status_code == 200:
                    categories["image"] = response.json().get("categories", [])
            except Exception as e:
                logger.warning(f"Could not fetch image categories: {str(e)}")
        
        return categories
        
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching categories: {str(e)}")

@router.get("/services/status")
async def get_services_status():
    """
    Get detailed status of all moderation services
    """
    try:
        services = {}
        
        async with httpx.AsyncClient() as client:
            # Check text service
            try:
                response = await client.get(f"{TEXT_SERVICE_URL}/health", timeout=5.0)
                services["text_moderation"] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                    "url": TEXT_SERVICE_URL
                }
            except Exception as e:
                services["text_moderation"] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "url": TEXT_SERVICE_URL
                }
            
            # Check image service
            try:
                response = await client.get(f"{IMAGE_SERVICE_URL}/health", timeout=5.0)
                services["image_moderation"] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                    "url": IMAGE_SERVICE_URL
                }
            except Exception as e:
                services["image_moderation"] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "url": IMAGE_SERVICE_URL
                }
        
        return services
        
    except Exception as e:
        logger.error(f"Error checking services status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error checking services: {str(e)}")
