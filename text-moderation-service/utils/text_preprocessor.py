"""
Text Preprocessing Utilities
Functions for cleaning and preparing text for moderation
"""

import re
import string
import logging

logger = logging.getLogger(__name__)

def preprocess_text(text: str) -> str:
    """
    Preprocess text for moderation analysis
    
    Args:
        text: Raw input text
        
    Returns:
        Preprocessed text
    """
    if not text:
        return ""
    
    try:
        # Convert to lowercase for consistency
        processed_text = text.lower()
        
        # Remove excessive whitespace
        processed_text = re.sub(r'\s+', ' ', processed_text)
        
        # Remove leading/trailing whitespace
        processed_text = processed_text.strip()
        
        # Handle common character substitutions used to bypass filters
        processed_text = handle_character_substitutions(processed_text)
        
        # Remove URLs (but keep them for context if needed)
        processed_text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '[URL]', processed_text)
        
        # Remove email addresses
        processed_text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', processed_text)
        
        logger.debug(f"Preprocessed text: '{text}' -> '{processed_text}'")
        return processed_text
        
    except Exception as e:
        logger.error(f"Error preprocessing text: {str(e)}")
        return text  # Return original text if preprocessing fails

def handle_character_substitutions(text: str) -> str:
    """
    Handle common character substitutions used to bypass content filters
    
    Args:
        text: Input text with potential character substitutions
        
    Returns:
        Text with substitutions normalized
    """
    substitutions = {
        '@': 'a',
        '3': 'e',
        '1': 'i',
        '!': 'i',
        '0': 'o',
        '5': 's',
        '7': 't',
        '4': 'a',
        '$': 's',
        '+': 't',
    }
    
    # Apply substitutions
    for sub, original in substitutions.items():
        text = text.replace(sub, original)
    
    return text

def extract_features(text: str) -> dict:
    """
    Extract features from text for analysis
    
    Args:
        text: Input text
        
    Returns:
        Dictionary of extracted features
    """
    features = {
        'length': len(text),
        'word_count': len(text.split()),
        'uppercase_ratio': sum(1 for c in text if c.isupper()) / len(text) if text else 0,
        'punctuation_ratio': sum(1 for c in text if c in string.punctuation) / len(text) if text else 0,
        'digit_ratio': sum(1 for c in text if c.isdigit()) / len(text) if text else 0,
        'has_urls': bool(re.search(r'http[s]?://', text)),
        'has_emails': bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)),
        'excessive_caps': sum(1 for c in text if c.isupper()) / len(text) > 0.5 if text else False,
        'repeated_chars': bool(re.search(r'(.)\1{3,}', text)),  # 4+ repeated characters
    }
    
    return features

def clean_text_for_display(text: str) -> str:
    """
    Clean text for safe display (remove potential harmful content)
    
    Args:
        text: Input text
        
    Returns:
        Cleaned text safe for display
    """
    # Remove potential script tags
    text = re.sub(r'<script.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Limit length for display
    if len(text) > 1000:
        text = text[:1000] + "..."
    
    return text
