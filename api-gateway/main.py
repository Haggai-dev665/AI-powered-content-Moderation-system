"""
API Gateway
Main entry point that routes requests to appropriate microservices
"""

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import httpx
import logging
from routes.gateway_routes import router as gateway_router
from typing import Optional
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Content Moderation API Gateway",
    description="Central gateway for AI-powered content moderation services",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include gateway routes
app.include_router(gateway_router, prefix="/api/v1", tags=["gateway"])

# Service URLs (configurable via environment variables)
TEXT_SERVICE_URL = os.getenv("TEXT_SERVICE_URL", "http://localhost:8001")
IMAGE_SERVICE_URL = os.getenv("IMAGE_SERVICE_URL", "http://localhost:8002")

@app.get("/health")
async def health_check():
    """Health check endpoint that verifies all services"""
    services_status = {}
    
    try:
        # Check text moderation service
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{TEXT_SERVICE_URL}/health", timeout=5.0)
                services_status["text_moderation"] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "url": TEXT_SERVICE_URL
                }
            except Exception as e:
                services_status["text_moderation"] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "url": TEXT_SERVICE_URL
                }
            
            # Check image moderation service
            try:
                response = await client.get(f"{IMAGE_SERVICE_URL}/health", timeout=5.0)
                services_status["image_moderation"] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "url": IMAGE_SERVICE_URL
                }
            except Exception as e:
                services_status["image_moderation"] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "url": IMAGE_SERVICE_URL
                }
        
        # Determine overall health
        all_healthy = all(service["status"] == "healthy" for service in services_status.values())
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "services": services_status,
            "gateway": "healthy"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "error": str(e),
                "services": services_status
            }
        )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Content Moderation API Gateway",
        "version": "1.0.0",
        "endpoints": {
            "text_moderation": "/api/v1/moderate/text",
            "image_moderation": "/api/v1/moderate/image",
            "health": "/health",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
