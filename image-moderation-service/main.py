"""
Image Moderation Service
Main entry point for the image moderation microservice
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from api.image_moderation import router as image_router
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Image Moderation Service",
    description="AI-powered image content moderation service",
    version="1.0.0"
)

# Include API routes
app.include_router(image_router, prefix="/api/v1", tags=["image-moderation"])

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "image-moderation"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Image Moderation Service is running"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )
