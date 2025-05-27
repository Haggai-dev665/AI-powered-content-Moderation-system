"""
Text Classification Model
Uses Hugging Face transformers for text moderation
"""

import logging
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
from typing import Dict, List
import asyncio

logger = logging.getLogger(__name__)

class TextModerationModel:
    def __init__(self):
        """Initialize the text moderation model"""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")
        
        # Load pre-trained toxicity classifier
        try:
            # Using a lightweight toxicity classifier
            self.toxicity_classifier = pipeline(
                "text-classification",
                model="unitary/toxic-bert",
                device=0 if self.device == "cuda" else -1
            )
            logger.info("Toxicity classifier loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load toxic-bert, using alternative: {e}")
            # Fallback to a simpler model
            self.toxicity_classifier = pipeline(
                "text-classification",
                model="martin-ha/toxic-comment-model",
                device=0 if self.device == "cuda" else -1
            )
        
        # Define thresholds for different categories
        self.thresholds = {
            "toxicity": 0.7,
            "hate_speech": 0.6,
            "profanity": 0.5,
            "threat": 0.8,
            "sexual_content": 0.6
        }
        
        # Simple profanity word list (in production, use a comprehensive dataset)
        self.profanity_words = {
            "damn", "hell", "shit", "fuck", "bitch", "asshole", "bastard",
            "crap", "piss", "dick", "cock", "pussy", "whore", "slut"
        }
    
    async def moderate(self, text: str) -> Dict:
        """
        Moderate text content and return results
        """
        try:
            results = {
                "is_appropriate": True,
                "confidence_score": 0.0,
                "flagged_categories": []
            }
            
            # Check for profanity using simple word matching
            profanity_score = self._check_profanity(text)
            if profanity_score > 0:
                results["flagged_categories"].append("profanity")
                results["confidence_score"] = max(results["confidence_score"], profanity_score)
            
            # Use AI model for toxicity detection
            toxicity_result = await self._check_toxicity(text)
            if toxicity_result["is_toxic"]:
                results["flagged_categories"].extend(toxicity_result["categories"])
                results["confidence_score"] = max(results["confidence_score"], toxicity_result["score"])
            
            # Determine if content is appropriate
            results["is_appropriate"] = len(results["flagged_categories"]) == 0
            
            return results
            
        except Exception as e:
            logger.error(f"Error in text moderation: {str(e)}")
            # Return safe default
            return {
                "is_appropriate": False,
                "confidence_score": 1.0,
                "flagged_categories": ["error"]
            }
    
    def _check_profanity(self, text: str) -> float:
        """Check for profanity using simple word matching"""
        text_lower = text.lower()
        found_words = [word for word in self.profanity_words if word in text_lower]
        
        if found_words:
            # Simple scoring based on number of profane words
            score = min(len(found_words) * 0.3, 1.0)
            logger.info(f"Profanity detected: {found_words}, score: {score}")
            return score
        
        return 0.0
    
    async def _check_toxicity(self, text: str) -> Dict:
        """Check for toxicity using AI model"""
        try:
            # Run toxicity classification
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.toxicity_classifier, text
            )
            
            # Parse results (different models may have different label formats)
            toxic_score = 0.0
            categories = []
            
            for prediction in result:
                label = prediction["label"].lower()
                score = prediction["score"]
                
                if "toxic" in label or "negative" in label:
                    toxic_score = max(toxic_score, score)
                    if score > self.thresholds["toxicity"]:
                        categories.append("toxic")
            
            return {
                "is_toxic": toxic_score > self.thresholds["toxicity"],
                "score": toxic_score,
                "categories": categories
            }
            
        except Exception as e:
            logger.error(f"Error in toxicity detection: {str(e)}")
            return {
                "is_toxic": False,
                "score": 0.0,
                "categories": []
            }
