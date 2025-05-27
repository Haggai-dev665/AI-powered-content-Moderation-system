"""
Image Classification Model
Uses computer vision models for image content moderation
"""

import logging
import numpy as np
import cv2
from PIL import Image
import torch
import torchvision.transforms as transforms
from typing import Dict, List
import asyncio
import io

logger = logging.getLogger(__name__)

class ImageModerationModel:
    def __init__(self):
        """Initialize the image moderation model"""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")
        
        # Define image preprocessing transforms
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        # Initialize models (using rule-based detection for now due to free tier limitations)
        self.skin_detector = SkinDetector()
        self.violence_detector = ViolenceDetector()
        
        # Define thresholds for different categories
        self.thresholds = {
            "explicit_content": 0.6,
            "violence": 0.7,
            "weapons": 0.8,
            "drugs": 0.7,
            "hate_symbols": 0.9
        }
    
    async def moderate(self, image_data: bytes) -> Dict:
        """
        Moderate image content and return results
        """
        try:
            results = {
                "is_appropriate": True,
                "confidence_score": 0.0,
                "flagged_categories": []
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
            
            # Check for weapons (basic edge detection for metallic objects)
            weapon_result = await self._check_weapons(cv_image)
            if weapon_result["has_weapons"]:
                results["flagged_categories"].append("weapons")
                results["confidence_score"] = max(results["confidence_score"], weapon_result["score"])
            
            # Determine if content is appropriate
            results["is_appropriate"] = len(results["flagged_categories"]) == 0
            
            return results
            
        except Exception as e:
            logger.error(f"Error in image moderation: {str(e)}")
            # Return safe default
            return {
                "is_appropriate": False,
                "confidence_score": 1.0,
                "flagged_categories": ["error"]
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
