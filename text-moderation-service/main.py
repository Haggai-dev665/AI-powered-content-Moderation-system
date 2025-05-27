"""
Text Moderation Service
Main entry point for the text moderation microservice
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from api.text_moderation import router as text_router
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Text Moderation Service",
    description="AI-powered text content moderation service",
    version="1.0.0"
)

# Include API routes
app.include_router(text_router, prefix="/api/v1", tags=["text-moderation"])

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "text-moderation"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Text Moderation Service is running"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
