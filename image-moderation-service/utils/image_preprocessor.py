"""
Image Preprocessing Utilities
Functions for cleaning and preparing images for moderation
"""

import cv2
import numpy as np
from PIL import Image, ExifTags
import io
import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

def validate_image(image_data: bytes) -> Dict:
    """
    Validate image data and extract basic information
    
    Args:
        image_data: Raw image bytes
        
    Returns:
        Dictionary with validation results and image info
    """
    try:
        # Try to open image with PIL
        image = Image.open(io.BytesIO(image_data))
        
        # Get basic image info
        width, height = image.size
        format_name = image.format
        mode = image.mode
        
        # Check file size (10MB limit)
        file_size_mb = len(image_data) / (1024 * 1024)
        if file_size_mb > 10:
            return {
                "is_valid": False,
                "error": f"File size too large: {file_size_mb:.1f}MB (max 10MB)",
                "file_size_mb": file_size_mb
            }
        
        # Check dimensions (4096x4096 limit)
        if width > 4096 or height > 4096:
            return {
                "is_valid": False,
                "error": f"Image dimensions too large: {width}x{height} (max 4096x4096)",
                "width": width,
                "height": height
            }
        
        # Check if image is too small
        if width < 32 or height < 32:
            return {
                "is_valid": False,
                "error": f"Image too small: {width}x{height} (min 32x32)",
                "width": width,
                "height": height
            }
        
        return {
            "is_valid": True,
            "width": width,
            "height": height,
            "format": format_name,
            "mode": mode,
            "file_size_mb": file_size_mb,
            "total_pixels": width * height
        }
        
    except Exception as e:
        logger.error(f"Error validating image: {str(e)}")
        return {
            "is_valid": False,
            "error": f"Invalid image format: {str(e)}"
        }

def preprocess_image(image_data: bytes) -> bytes:
    """
    Preprocess image for moderation analysis
    
    Args:
        image_data: Raw image bytes
        
    Returns:
        Preprocessed image bytes
    """
    try:
        # Open image
        image = Image.open(io.BytesIO(image_data))
        
        # Handle EXIF orientation
        image = fix_image_orientation(image)
        
        # Convert to RGB if necessary
        if image.mode not in ['RGB', 'L']:
            image = image.convert('RGB')
        
        # Resize if too large (for processing efficiency)
        max_size = 1024
        if max(image.size) > max_size:
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            logger.info(f"Resized image to {image.size}")
        
        # Convert back to bytes
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=85)
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"Error preprocessing image: {str(e)}")
        return image_data  # Return original if preprocessing fails

def fix_image_orientation(image: Image.Image) -> Image.Image:
    """
    Fix image orientation based on EXIF data
    
    Args:
        image: PIL Image object
        
    Returns:
        Image with corrected orientation
    """
    try:
        # Check if image has EXIF data
        if hasattr(image, '_getexif') and image._getexif() is not None:
            exif = image._getexif()
            
            # Look for orientation tag
            for tag, value in exif.items():
                if tag in ExifTags.TAGS and ExifTags.TAGS[tag] == 'Orientation':
                    if value == 3:
                        image = image.rotate(180, expand=True)
                    elif value == 6:
                        image = image.rotate(270, expand=True)
                    elif value == 8:
                        image = image.rotate(90, expand=True)
                    break
        
        return image
        
    except Exception as e:
        logger.warning(f"Could not fix image orientation: {str(e)}")
        return image

def extract_image_features(image_data: bytes) -> Dict:
    """
    Extract features from image for analysis
    
    Args:
        image_data: Raw image bytes
        
    Returns:
        Dictionary of extracted features
    """
    try:
        # Open image
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to numpy array for OpenCV operations
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Basic features
        height, width = cv_image.shape[:2]
        aspect_ratio = width / height
        
        # Color analysis
        mean_color = np.mean(cv_image, axis=(0, 1))
        
        # Brightness analysis
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray)
        
        # Contrast analysis
        contrast = np.std(gray)
        
        # Edge density
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        # Color distribution
        hist_b = cv2.calcHist([cv_image], [0], None, [256], [0, 256])
        hist_g = cv2.calcHist([cv_image], [1], None, [256], [0, 256])
        hist_r = cv2.calcHist([cv_image], [2], None, [256], [0, 256])
        
        # Dominant colors (simplified)
        dominant_blue = np.argmax(hist_b)
        dominant_green = np.argmax(hist_g)
        dominant_red = np.argmax(hist_r)
        
        return {
            'width': width,
            'height': height,
            'aspect_ratio': aspect_ratio,
            'brightness': float(brightness),
            'contrast': float(contrast),
            'edge_density': float(edge_density),
            'mean_color_bgr': [float(x) for x in mean_color],
            'dominant_colors': {
                'blue': int(dominant_blue),
                'green': int(dominant_green),
                'red': int(dominant_red)
            }
        }
        
    except Exception as e:
        logger.error(f"Error extracting image features: {str(e)}")
        return {}

def resize_image(image_data: bytes, target_size: Tuple[int, int]) -> bytes:
    """
    Resize image to target dimensions
    
    Args:
        image_data: Raw image bytes
        target_size: Target (width, height)
        
    Returns:
        Resized image bytes
    """
    try:
        image = Image.open(io.BytesIO(image_data))
        resized_image = image.resize(target_size, Image.Resampling.LANCZOS)
        
        output = io.BytesIO()
        resized_image.save(output, format='JPEG', quality=85)
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"Error resizing image: {str(e)}")
        return image_data

def create_thumbnail(image_data: bytes, size: int = 150) -> bytes:
    """
    Create a thumbnail of the image
    
    Args:
        image_data: Raw image bytes
        size: Maximum dimension for thumbnail
        
    Returns:
        Thumbnail image bytes
    """
    try:
        image = Image.open(io.BytesIO(image_data))
        image.thumbnail((size, size), Image.Resampling.LANCZOS)
        
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=70)
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"Error creating thumbnail: {str(e)}")
        return image_data
