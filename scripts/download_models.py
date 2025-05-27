"""
Script to download and cache AI models
"""

import os
import logging
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_text_models():
    """Download text moderation models"""
    logger.info("Downloading text moderation models...")
    
    models_to_download = [
        "unitary/toxic-bert",
        "martin-ha/toxic-comment-model"
    ]
    
    for model_name in models_to_download:
        try:
            logger.info(f"Downloading model: {model_name}")
            
            # Download tokenizer and model
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSequenceClassification.from_pretrained(model_name)
            
            # Create pipeline to cache everything
            classifier = pipeline(
                "text-classification",
                model=model,
                tokenizer=tokenizer,
                device=-1  # CPU only for downloading
            )
            
            # Test the model with a simple input
            test_result = classifier("This is a test message")
            logger.info(f"Model {model_name} downloaded and tested successfully")
            
        except Exception as e:
            logger.warning(f"Failed to download {model_name}: {str(e)}")
            logger.info("Will use fallback model at runtime")

def download_image_models():
    """Download image moderation models"""
    logger.info("Image models will be initialized at runtime")
    logger.info("OpenCV and basic computer vision models are built-in")

def setup_model_cache():
    """Setup model cache directory"""
    cache_dir = os.path.join(os.path.dirname(__file__), "..", "models", "cache")
    os.makedirs(cache_dir, exist_ok=True)
    
    # Set Hugging Face cache directory
    os.environ["TRANSFORMERS_CACHE"] = cache_dir
    os.environ["HF_HOME"] = cache_dir
    
    logger.info(f"Model cache directory: {cache_dir}")
    return cache_dir

def main():
    """Main function to download all models"""
    logger.info("Starting model download process...")
    
    # Setup cache
    cache_dir = setup_model_cache()
    
    # Download models
    download_text_models()
    download_image_models()
    
    logger.info("Model download process completed!")
    logger.info(f"Models cached in: {cache_dir}")

if __name__ == "__main__":
    main()
