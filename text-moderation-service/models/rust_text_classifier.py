"""
Rust-based Text Classification Model
Provides high-performance offline text moderation using Rust
"""

import logging
import sys
import os
from typing import Dict, List
import asyncio

# Add the Rust module to Python path
rust_lib_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                             "rust-moderation", "target", "release")
if os.path.exists(rust_lib_path):
    sys.path.insert(0, rust_lib_path)

try:
    # Try to import the Rust module
    import rust_moderation
    RUST_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("Rust moderation module loaded successfully")
except ImportError as e:
    RUST_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"Rust moderation module not available: {e}. Falling back to Python implementation.")

class RustTextModerationModel:
    """High-performance text moderation using Rust backend"""
    
    def __init__(self):
        """Initialize the Rust-based text moderation model"""
        self.rust_available = RUST_AVAILABLE
        
        if self.rust_available:
            try:
                self.moderator = rust_moderation.TextModerator()
                logger.info("Rust TextModerator initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Rust TextModerator: {e}")
                self.rust_available = False
                self._init_fallback()
        else:
            self._init_fallback()
    
    def _init_fallback(self):
        """Initialize fallback Python-based moderation"""
        logger.info("Initializing Python fallback moderation")
        
        # Simple profanity word list
        self.profanity_words = {
            "damn", "hell", "shit", "fuck", "fucking", "bitch", "asshole", "bastard",
            "crap", "piss", "dick", "cock", "pussy", "whore", "slut", "retard",
            "idiot", "stupid", "dumb", "moron", "nazi", "terrorist", "kill yourself",
            "kys", "suicide", "murder", "rape", "molest", "pedophile"
        }
        
        # Threat keywords
        self.threat_words = {
            "kill", "murder", "shoot", "stab", "bomb", "terror", "violence",
            "harm", "hurt", "destroy", "death"
        }
        
        # Spam keywords
        self.spam_words = {
            "buy now", "click here", "free money", "viagra", "casino", 
            "lottery", "winner", "prize"
        }
    
    async def moderate(self, text: str) -> Dict:
        """
        Moderate text content and return results
        """
        try:
            if self.rust_available:
                return await self._moderate_with_rust(text)
            else:
                return await self._moderate_with_python(text)
        except Exception as e:
            logger.error(f"Error in text moderation: {str(e)}")
            # Return safe default
            return {
                "is_appropriate": False,
                "confidence_score": 1.0,
                "flagged_categories": ["error"],
                "processed_text": text
            }
    
    async def _moderate_with_rust(self, text: str) -> Dict:
        """Use Rust moderation"""
        try:
            # Run Rust moderation in executor to avoid blocking
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.moderator.moderate_text, text
            )
            
            # Convert Rust result to Python dict
            return {
                "is_appropriate": result.is_appropriate,
                "confidence_score": result.confidence_score,
                "flagged_categories": result.flagged_categories,
                "processed_text": result.processed_text
            }
        except Exception as e:
            logger.error(f"Rust moderation failed: {e}")
            # Fallback to Python
            return await self._moderate_with_python(text)
    
    async def _moderate_with_python(self, text: str) -> Dict:
        """Fallback Python moderation"""
        results = {
            "is_appropriate": True,
            "confidence_score": 0.0,
            "flagged_categories": [],
            "processed_text": text.strip().lower()
        }
        
        text_lower = text.lower()
        
        # Check profanity
        profanity_score = self._check_profanity_python(text_lower)
        if profanity_score > 0:
            results["flagged_categories"].append("profanity")
            results["confidence_score"] = max(results["confidence_score"], profanity_score)
        
        # Check threats
        threat_score = self._check_threats_python(text_lower)
        if threat_score > 0:
            results["flagged_categories"].append("threats")
            results["confidence_score"] = max(results["confidence_score"], threat_score)
        
        # Check spam
        spam_score = self._check_spam_python(text_lower)
        if spam_score > 0:
            results["flagged_categories"].append("spam")
            results["confidence_score"] = max(results["confidence_score"], spam_score)
        
        # Check excessive caps
        if self._has_excessive_caps(text):
            results["flagged_categories"].append("excessive_caps")
            results["confidence_score"] = max(results["confidence_score"], 0.3)
        
        # Determine if content is appropriate
        results["is_appropriate"] = len(results["flagged_categories"]) == 0
        
        return results
    
    def _check_profanity_python(self, text: str) -> float:
        """Simple Python profanity detection"""
        found_words = []
        words = text.split()
        
        for word in words:
            # Remove punctuation and check
            clean_word = ''.join(c for c in word if c.isalnum())
            if clean_word in self.profanity_words:
                found_words.append(clean_word)
        
        if found_words:
            # Score based on number of profane words
            score = min(len(found_words) * 0.3, 1.0)
            logger.info(f"Profanity detected: {found_words}, score: {score}")
            return score
        
        return 0.0
    
    def _check_threats_python(self, text: str) -> float:
        """Simple Python threat detection"""
        score = 0.0
        
        for threat_word in self.threat_words:
            if threat_word in text:
                score += 0.4
        
        # Check for specific threat patterns
        threat_patterns = [
            "kill you", "murder you", "going to kill", "i will kill",
            "death threat", "violence against"
        ]
        
        for pattern in threat_patterns:
            if pattern in text:
                score += 0.6
        
        return min(score, 1.0)
    
    def _check_spam_python(self, text: str) -> float:
        """Simple Python spam detection"""
        score = 0.0
        
        for spam_word in self.spam_words:
            if spam_word in text:
                score += 0.3
        
        # Check for URLs
        if "http" in text or "www." in text or ".com" in text:
            score += 0.4
        
        return min(score, 1.0)
    
    def _has_excessive_caps(self, text: str) -> bool:
        """Check for excessive capitalization"""
        if len(text) < 10:
            return False
        
        caps_count = sum(1 for c in text if c.isupper())
        total_chars = len([c for c in text if c.isalpha()])
        
        if total_chars == 0:
            return False
        
        caps_ratio = caps_count / total_chars
        return caps_ratio > 0.6
    
    async def moderate_batch(self, texts: List[str]) -> List[Dict]:
        """Moderate multiple texts"""
        if self.rust_available:
            try:
                # Use Rust batch processing
                results = await asyncio.get_event_loop().run_in_executor(
                    None, self.moderator.moderate_batch, texts
                )
                
                return [
                    {
                        "is_appropriate": result.is_appropriate,
                        "confidence_score": result.confidence_score,
                        "flagged_categories": result.flagged_categories,
                        "processed_text": result.processed_text
                    }
                    for result in results
                ]
            except Exception as e:
                logger.error(f"Rust batch moderation failed: {e}")
                # Fall through to Python implementation
        
        # Python fallback - process sequentially
        results = []
        for text in texts:
            result = await self._moderate_with_python(text)
            results.append(result)
        
        return results
    
    def is_rust_available(self) -> bool:
        """Check if Rust backend is available"""
        return self.rust_available
    
    def get_backend_info(self) -> Dict:
        """Get information about the backend"""
        return {
            "rust_available": self.rust_available,
            "backend": "Rust" if self.rust_available else "Python",
            "features": ["profanity_detection", "threat_detection", "spam_detection", "caps_detection"]
        }