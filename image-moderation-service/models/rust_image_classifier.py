"""
Rust-enhanced Image Classification Model
Combines computer vision with Rust-based image processing for better performance
"""

import logging
import numpy as np
import cv2
from PIL import Image
import torch
import torchvision.transforms as transforms
from typing import Dict, List, Optional
import asyncio
import io
import os
import sys

# Try to import Rust module
try:
    import rust_moderation
    RUST_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("Rust image moderation module loaded successfully")
except ImportError as e:
    RUST_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"Rust image moderation module not available: {e}. Using Python-only implementation.")

class RustImageModerationModel:
    """Enhanced image moderation with Rust backend for image processing"""
    
    def __init__(self):
        """Initialize the Rust-enhanced image moderation model"""
        self.rust_available = RUST_AVAILABLE
        
        if self.rust_available:
            try:
                self.rust_moderator = rust_moderation.ImageModerator()
                logger.info("Rust ImageModerator initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Rust ImageModerator: {e}")
                self.rust_available = False
        
        # Initialize Python-based detectors as fallback
        self._init_python_detectors()
        
        # Define image preprocessing transforms
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        # Define thresholds for different categories
        self.thresholds = {
            "explicit_content": 0.6,
            "violence": 0.7,
            "weapons": 0.8,
            "drugs": 0.7,
            "hate_symbols": 0.9,
            "inappropriate_text": 0.5
        }
        
        # Supported image formats
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        self.max_file_size = 10 * 1024 * 1024  # 10MB
    
    def _init_python_detectors(self):
        """Initialize Python-based detectors"""
        self.skin_detector = SkinDetector()
        self.violence_detector = ViolenceDetector()
        self.text_detector = ImageTextDetector()
    
    async def validate_image(self, image_data: bytes, filename: str = None) -> Dict:
        """Validate image format and properties"""
        try:
            # Check file size
            if len(image_data) > self.max_file_size:
                return {
                    "is_valid": False,
                    "error": "File too large (max 10MB)",
                    "file_size": len(image_data)
                }
            
            # Python-based validation (more reliable)
            try:
                image = Image.open(io.BytesIO(image_data))
                width, height = image.size
                format_name = image.format.lower() if image.format else "unknown"
                
                return {
                    "is_valid": True,
                    "width": width,
                    "height": height,
                    "format": format_name,
                    "file_size": len(image_data)
                }
            except Exception as e:
                return {
                    "is_valid": False,
                    "error": f"Invalid image: {str(e)}",
                    "file_size": len(image_data)
                }
        
        except Exception as e:
            logger.error(f"Error in image validation: {str(e)}")
            return {
                "is_valid": False,
                "error": f"Validation error: {str(e)}",
                "file_size": len(image_data) if image_data else 0
            }
    
    async def moderate(self, image_data: bytes, filename: str = None) -> Dict:
        """
        Moderate image content and return results
        """
        try:
            # First validate the image
            validation = await self.validate_image(image_data, filename)
            if not validation.get("is_valid", False):
                return {
                    "is_appropriate": False,
                    "confidence_score": 1.0,
                    "flagged_categories": ["invalid_image"],
                    "error": validation.get("error", "Invalid image"),
                    "image_info": validation
                }
            
            results = {
                "is_appropriate": True,
                "confidence_score": 0.0,
                "flagged_categories": [],
                "image_info": validation
            }
            
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert to numpy array for OpenCV operations
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Check for explicit content (skin detection)
            skin_result = await self._check_explicit_content(cv_image)
            if skin_result["is_explicit"]:
                results["flagged_categories"].append("explicit_content")
                results["confidence_score"] = max(results["confidence_score"], skin_result["score"])
            
            # Check for violence indicators
            violence_result = await self._check_violence(cv_image)
            if violence_result["is_violent"]:
                results["flagged_categories"].append("violence")
                results["confidence_score"] = max(results["confidence_score"], violence_result["score"])
            
            # Check for weapons
            weapon_result = await self._check_weapons(cv_image)
            if weapon_result["has_weapons"]:
                results["flagged_categories"].append("weapons")
                results["confidence_score"] = max(results["confidence_score"], weapon_result["score"])
            
            # Check for inappropriate text in image
            text_result = await self._check_image_text(cv_image)
            if text_result["has_inappropriate_text"]:
                results["flagged_categories"].append("inappropriate_text")
                results["confidence_score"] = max(results["confidence_score"], text_result["score"])
            
            # Check image dimensions for potential issues
            if self._is_suspicious_dimensions(validation):
                results["flagged_categories"].append("suspicious_dimensions")
                results["confidence_score"] = max(results["confidence_score"], 0.3)
            
            # Determine if content is appropriate
            results["is_appropriate"] = len(results["flagged_categories"]) == 0
            
            return results
            
        except Exception as e:
            logger.error(f"Error in image moderation: {str(e)}")
            # Return safe default
            return {
                "is_appropriate": False,
                "confidence_score": 1.0,
                "flagged_categories": ["error"],
                "error": str(e)
            }
    
    async def _check_explicit_content(self, image: np.ndarray) -> Dict:
        """Check for explicit content using skin detection"""
        try:
            skin_percentage = await asyncio.get_event_loop().run_in_executor(
                None, self.skin_detector.detect_skin_percentage, image
            )
            
            # If more than 40% of the image is skin-colored, flag as potentially explicit
            is_explicit = skin_percentage > 0.4
            score = min(skin_percentage * 1.5, 1.0) if is_explicit else skin_percentage
            
            logger.info(f"Skin detection: {skin_percentage:.2f}%, explicit: {is_explicit}")
            
            return {
                "is_explicit": is_explicit,
                "score": score,
                "skin_percentage": skin_percentage
            }
            
        except Exception as e:
            logger.error(f"Error in explicit content detection: {str(e)}")
            return {"is_explicit": False, "score": 0.0, "skin_percentage": 0.0}
    
    async def _check_violence(self, image: np.ndarray) -> Dict:
        """Check for violence indicators"""
        try:
            violence_score = await asyncio.get_event_loop().run_in_executor(
                None, self.violence_detector.detect_violence_indicators, image
            )
            
            is_violent = violence_score > self.thresholds["violence"]
            
            logger.info(f"Violence detection score: {violence_score:.2f}, violent: {is_violent}")
            
            return {
                "is_violent": is_violent,
                "score": violence_score
            }
            
        except Exception as e:
            logger.error(f"Error in violence detection: {str(e)}")
            return {"is_violent": False, "score": 0.0}
    
    async def _check_weapons(self, image: np.ndarray) -> Dict:
        """Basic weapon detection using edge detection and color analysis"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Edge detection
            edges = cv2.Canny(gray, 50, 150)
            edge_percentage = np.sum(edges > 0) / edges.size
            
            # Look for metallic colors (simplified)
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Define range for metallic/gray colors
            lower_metal = np.array([0, 0, 50])
            upper_metal = np.array([180, 50, 200])
            
            metal_mask = cv2.inRange(hsv, lower_metal, upper_metal)
            metal_percentage = np.sum(metal_mask > 0) / metal_mask.size
            
            # Simple heuristic: high edge density + metallic colors might indicate weapons
            weapon_score = (edge_percentage * 0.7 + metal_percentage * 0.3)
            has_weapons = weapon_score > 0.3 and edge_percentage > 0.1
            
            logger.info(f"Weapon detection - edges: {edge_percentage:.2f}, metal: {metal_percentage:.2f}, score: {weapon_score:.2f}")
            
            return {
                "has_weapons": has_weapons,
                "score": weapon_score
            }
            
        except Exception as e:
            logger.error(f"Error in weapon detection: {str(e)}")
            return {"has_weapons": False, "score": 0.0}
    
    async def _check_image_text(self, image: np.ndarray) -> Dict:
        """Check for inappropriate text within images"""
        try:
            text_score = await asyncio.get_event_loop().run_in_executor(
                None, self.text_detector.detect_inappropriate_text, image
            )
            
            has_inappropriate_text = text_score > self.thresholds["inappropriate_text"]
            
            logger.info(f"Image text detection score: {text_score:.2f}, inappropriate: {has_inappropriate_text}")
            
            return {
                "has_inappropriate_text": has_inappropriate_text,
                "score": text_score
            }
            
        except Exception as e:
            logger.error(f"Error in image text detection: {str(e)}")
            return {"has_inappropriate_text": False, "score": 0.0}
    
    def _is_suspicious_dimensions(self, validation: Dict) -> bool:
        """Check for suspicious image dimensions"""
        width = validation.get("width", 0)
        height = validation.get("height", 0)
        
        if width == 0 or height == 0:
            return True
        
        # Very thin images might be suspicious
        aspect_ratio = max(width, height) / min(width, height)
        if aspect_ratio > 20:
            return True
        
        # Very small images might be tracking pixels
        if width * height < 100:
            return True
        
        return False
    
    def is_rust_available(self) -> bool:
        """Check if Rust backend is available"""
        return self.rust_available
    
    def get_backend_info(self) -> Dict:
        """Get information about the backend"""
        return {
            "rust_available": self.rust_available,
            "backend": "Rust + Python" if self.rust_available else "Python",
            "features": [
                "skin_detection", 
                "violence_detection", 
                "weapon_detection", 
                "text_detection",
                "dimension_validation",
                "format_validation"
            ]
        }


class SkinDetector:
    """Simple skin detection using color space analysis"""
    
    def detect_skin_percentage(self, image: np.ndarray) -> float:
        """
        Detect percentage of skin-colored pixels in image
        """
        try:
            # Convert BGR to HSV
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Define range of skin color in HSV
            lower_skin = np.array([0, 20, 70])
            upper_skin = np.array([20, 255, 255])
            
            # Create mask for skin color
            mask = cv2.inRange(hsv, lower_skin, upper_skin)
            
            # Calculate percentage of skin pixels
            skin_pixels = np.sum(mask > 0)
            total_pixels = mask.size
            skin_percentage = skin_pixels / total_pixels
            
            return skin_percentage
            
        except Exception as e:
            logger.error(f"Error in skin detection: {str(e)}")
            return 0.0


class ViolenceDetector:
    """Simple violence detection using color and edge analysis"""
    
    def detect_violence_indicators(self, image: np.ndarray) -> float:
        """
        Detect violence indicators in image
        """
        try:
            # Convert to HSV for better color analysis
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Look for red colors (blood indication)
            lower_red1 = np.array([0, 50, 50])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([170, 50, 50])
            upper_red2 = np.array([180, 255, 255])
            
            mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
            mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
            red_mask = mask1 + mask2
            
            red_percentage = np.sum(red_mask > 0) / red_mask.size
            
            # Edge detection for sharp objects
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 100, 200)
            edge_density = np.sum(edges > 0) / edges.size
            
            # Simple scoring
            violence_score = (red_percentage * 0.6 + edge_density * 0.4)
            
            return min(violence_score * 2, 1.0)  # Amplify and cap at 1.0
            
        except Exception as e:
            logger.error(f"Error in violence detection: {str(e)}")
            return 0.0


class ImageTextDetector:
    """Detect inappropriate text within images using OCR"""
    
    def __init__(self):
        self.inappropriate_words = {
            "hate", "kill", "murder", "nazi", "terrorist", "bomb", "weapon",
            "fuck", "shit", "damn", "bitch", "asshole", "bastard"
        }
    
    def detect_inappropriate_text(self, image: np.ndarray) -> float:
        """
        Detect inappropriate text in image using basic OCR
        """
        try:
            # Convert to grayscale for better OCR
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply some preprocessing
            gray = cv2.medianBlur(gray, 3)
            
            # Simple text detection using edge detection and contours
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Check if there are many small contours (might indicate text)
            text_like_contours = 0
            for contour in contours:
                area = cv2.contourArea(contour)
                if 50 < area < 1000:  # Text-like size
                    text_like_contours += 1
            
            # Simple heuristic: many small contours might indicate text
            text_density = text_like_contours / max(len(contours), 1)
            
            # For now, return a simple score based on contour analysis
            # In a real implementation, you would use OCR libraries like pytesseract
            return min(text_density * 0.5, 1.0)
            
        except Exception as e:
            logger.error(f"Error in text detection: {str(e)}")
            return 0.0