//! Rust-based Content Moderation Library
//! 
//! This library provides high-performance content moderation capabilities
//! with Python bindings for integration with the existing FastAPI services.

use pyo3::prelude::*;
use pyo3::types::PyDict;
use regex::Regex;
use rayon::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::HashSet;
use unicode_normalization::UnicodeNormalization;
use image::GenericImageView;

/// Text moderation result
#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass]
pub struct ModerationResult {
    #[pyo3(get, set)]
    pub is_appropriate: bool,
    #[pyo3(get, set)]
    pub confidence_score: f64,
    #[pyo3(get, set)]
    pub flagged_categories: Vec<String>,
    #[pyo3(get, set)]
    pub processed_text: String,
}

#[pymethods]
impl ModerationResult {
    #[new]
    fn new() -> Self {
        Self {
            is_appropriate: true,
            confidence_score: 0.0,
            flagged_categories: Vec::new(),
            processed_text: String::new(),
        }
    }
    
    fn to_dict(&self, py: Python) -> PyResult<PyObject> {
        let dict = PyDict::new(py);
        dict.set_item("is_appropriate", self.is_appropriate)?;
        dict.set_item("confidence_score", self.confidence_score)?;
        dict.set_item("flagged_categories", &self.flagged_categories)?;
        dict.set_item("processed_text", &self.processed_text)?;
        Ok(dict.into())
    }
}

/// High-performance text moderator
#[pyclass]
pub struct TextModerator {
    profanity_patterns: Vec<Regex>,
    profanity_words: HashSet<String>,
    threat_patterns: Vec<Regex>,
    spam_patterns: Vec<Regex>,
}

#[pymethods]
impl TextModerator {
    #[new]
    fn new() -> PyResult<Self> {
        let mut moderator = Self {
            profanity_patterns: Vec::new(),
            profanity_words: HashSet::new(),
            threat_patterns: Vec::new(),
            spam_patterns: Vec::new(),
        };
        
        moderator.initialize_patterns()?;
        Ok(moderator)
    }
    
    /// Moderate a single text string
    fn moderate_text(&self, text: &str) -> PyResult<ModerationResult> {
        self.moderate_text_internal(text)
    }
    
    /// Moderate multiple texts in parallel
    fn moderate_batch(&self, texts: Vec<&str>) -> PyResult<Vec<ModerationResult>> {
        let results: Result<Vec<_>, _> = texts
            .par_iter()
            .map(|text| self.moderate_text_internal(text))
            .collect();
        
        match results {
            Ok(results) => Ok(results),
            Err(e) => Err(e),
        }
    }
    
    /// Add custom profanity words
    fn add_profanity_words(&mut self, words: Vec<String>) -> PyResult<()> {
        for word in words {
            self.profanity_words.insert(word.to_lowercase());
        }
        Ok(())
    }
    
    /// Check if text contains profanity
    fn contains_profanity(&self, text: &str) -> bool {
        self.check_profanity(text).0
    }
    
    /// Get profanity score for text
    fn get_profanity_score(&self, text: &str) -> f64 {
        self.check_profanity(text).1
    }
}

impl TextModerator {
    fn initialize_patterns(&mut self) -> PyResult<()> {
        // Initialize profanity word list
        let profanity_words = vec![
            "damn", "hell", "shit", "fuck", "fucking", "bitch", "asshole", "bastard",
            "crap", "piss", "dick", "cock", "pussy", "whore", "slut", "retard",
            "idiot", "stupid", "dumb", "moron", "nazi", "terrorist", "kill yourself",
            "kys", "suicide", "murder", "rape", "molest", "pedophile", "faggot",
            "nigger", "nigga", "spic", "chink", "gook", "kike", "wetback",
        ];
        
        for word in profanity_words {
            self.profanity_words.insert(word.to_string());
        }
        
        // Compile regex patterns for profanity detection
        let profanity_regex_patterns = vec![
            r"\b(f+u+c+k+|s+h+i+t+|d+a+m+n+)\b",
            r"\b\w*[4@]ss\w*\b",
            r"\b\w*b[i1]tch\w*\b",
            r"\b\w*[5$]h[i1]t\w*\b",
        ];
        
        for pattern in profanity_regex_patterns {
            match Regex::new(pattern) {
                Ok(regex) => self.profanity_patterns.push(regex),
                Err(_) => continue,
            }
        }
        
        // Threat detection patterns
        let threat_patterns = vec![
            r"\b(kill|murder|shoot|stab|bomb|terror)\s+(you|him|her|them)\b",
            r"\bgoing\s+to\s+(kill|hurt|destroy)\b",
            r"\b(death|violence|harm)\s+threat\b",
            r"\bi\s+will\s+(kill|hurt|destroy)\b",
        ];
        
        for pattern in threat_patterns {
            match Regex::new(pattern) {
                Ok(regex) => self.threat_patterns.push(regex),
                Err(_) => continue,
            }
        }
        
        // Spam detection patterns
        let spam_patterns = vec![
            r"\b(buy\s+now|click\s+here|free\s+money)\b",
            r"\b(viagra|casino|lottery|winner)\b",
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
        ];
        
        for pattern in spam_patterns {
            match Regex::new(pattern) {
                Ok(regex) => self.spam_patterns.push(regex),
                Err(_) => continue,
            }
        }
        
        Ok(())
    }
    
    fn moderate_text_internal(&self, text: &str) -> PyResult<ModerationResult> {
        let mut result = ModerationResult::new();
        
        // Normalize text
        let normalized_text = self.normalize_text(text);
        result.processed_text = normalized_text.clone();
        
        let text_lower = normalized_text.to_lowercase();
        
        // Check profanity
        let (has_profanity, profanity_score) = self.check_profanity(&text_lower);
        if has_profanity {
            result.flagged_categories.push("profanity".to_string());
            result.confidence_score = result.confidence_score.max(profanity_score);
        }
        
        // Check threats
        let (has_threats, threat_score) = self.check_threats(&text_lower);
        if has_threats {
            result.flagged_categories.push("threats".to_string());
            result.confidence_score = result.confidence_score.max(threat_score);
        }
        
        // Check spam
        let (has_spam, spam_score) = self.check_spam(&text_lower);
        if has_spam {
            result.flagged_categories.push("spam".to_string());
            result.confidence_score = result.confidence_score.max(spam_score);
        }
        
        // Check excessive caps
        if self.has_excessive_caps(text) {
            result.flagged_categories.push("excessive_caps".to_string());
            result.confidence_score = result.confidence_score.max(0.3);
        }
        
        // Check repeated characters
        if self.has_repeated_chars(text) {
            result.flagged_categories.push("spam_chars".to_string());
            result.confidence_score = result.confidence_score.max(0.4);
        }
        
        result.is_appropriate = result.flagged_categories.is_empty();
        
        Ok(result)
    }
    
    fn normalize_text(&self, text: &str) -> String {
        // Unicode normalization and cleanup
        text.nfc()
            .collect::<String>()
            .trim()
            .to_string()
    }
    
    fn check_profanity(&self, text: &str) -> (bool, f64) {
        let mut score: f64 = 0.0;
        let mut matches = 0;
        
        // Check exact word matches
        for word in &self.profanity_words {
            let word_regex = format!(r"\b{}\b", regex::escape(word));
            if let Ok(regex) = Regex::new(&word_regex) {
                if regex.is_match(text) {
                    matches += 1;
                    score += 0.3;
                }
            }
        }
        
        // Check regex patterns for obfuscated profanity
        for pattern in &self.profanity_patterns {
            if pattern.is_match(text) {
                matches += 1;
                score += 0.4;
            }
        }
        
        // Cap the score
        score = score.min(1.0);
        
        (matches > 0, score)
    }
    
    fn check_threats(&self, text: &str) -> (bool, f64) {
        let mut score: f64 = 0.0;
        
        for pattern in &self.threat_patterns {
            if pattern.is_match(text) {
                score += 0.8;
            }
        }
        
        (score > 0.0, score.min(1.0))
    }
    
    fn check_spam(&self, text: &str) -> (bool, f64) {
        let mut score: f64 = 0.0;
        
        for pattern in &self.spam_patterns {
            if pattern.is_match(text) {
                score += 0.5;
            }
        }
        
        (score > 0.0, score.min(1.0))
    }
    
    fn has_excessive_caps(&self, text: &str) -> bool {
        let total_chars = text.chars().count();
        if total_chars < 10 {
            return false;
        }
        
        let caps_count = text.chars().filter(|c| c.is_uppercase()).count();
        let caps_ratio = caps_count as f64 / total_chars as f64;
        
        caps_ratio > 0.6
    }
    
    fn has_repeated_chars(&self, text: &str) -> bool {
        // Check for repeated characters (5+ in a row) without backreferences
        let chars: Vec<char> = text.chars().collect();
        let mut count = 1;
        
        for i in 1..chars.len() {
            if chars[i] == chars[i-1] {
                count += 1;
                if count >= 5 {
                    return true;
                }
            } else {
                count = 1;
            }
        }
        
        false
    }
}

/// Image moderation capabilities
#[pyclass]
pub struct ImageModerator {
    max_file_size: u64,
    allowed_formats: HashSet<String>,
}

#[pymethods]
impl ImageModerator {
    #[new]
    fn new() -> Self {
        let mut allowed_formats = HashSet::new();
        allowed_formats.insert("jpg".to_string());
        allowed_formats.insert("jpeg".to_string());
        allowed_formats.insert("png".to_string());
        allowed_formats.insert("gif".to_string());
        allowed_formats.insert("webp".to_string());
        
        Self {
            max_file_size: 10 * 1024 * 1024, // 10MB
            allowed_formats,
        }
    }
    
    /// Validate image file
    fn validate_image(&self, file_path: &str) -> PyResult<PyObject> {
        match self.validate_image_internal(file_path) {
            Ok(result) => {
                Python::with_gil(|py| {
                    let dict = PyDict::new(py);
                    dict.set_item("is_valid", result.0)?;
                    dict.set_item("message", result.1)?;
                    dict.set_item("file_info", result.2)?;
                    Ok(dict.into())
                })
            }
            Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Image validation failed: {}", e)))
        }
    }
    
    /// Get image metadata
    fn get_image_info(&self, file_path: &str) -> PyResult<PyObject> {
        match self.get_image_info_internal(file_path) {
            Ok(info) => {
                Python::with_gil(|py| {
                    let dict = PyDict::new(py);
                    dict.set_item("width", info.0)?;
                    dict.set_item("height", info.1)?;
                    dict.set_item("format", info.2)?;
                    dict.set_item("file_size", info.3)?;
                    Ok(dict.into())
                })
            }
            Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to get image info: {}", e)))
        }
    }
}

impl ImageModerator {
    fn validate_image_internal(&self, file_path: &str) -> Result<(bool, String, Option<(u32, u32, String, u64)>), Box<dyn std::error::Error>> {
        // Check file size
        let metadata = std::fs::metadata(file_path)?;
        if metadata.len() > self.max_file_size {
            return Ok((false, "File too large".to_string(), None));
        }
        
        // Try to open and validate image
        match image::open(file_path) {
            Ok(img) => {
                let (width, height) = img.dimensions();
                let format = image::guess_format(&std::fs::read(file_path)?)?;
                let format_str = format!("{:?}", format).to_lowercase();
                
                if !self.allowed_formats.contains(&format_str) {
                    return Ok((false, "Unsupported format".to_string(), None));
                }
                
                Ok((true, "Valid image".to_string(), Some((width, height, format_str, metadata.len()))))
            }
            Err(e) => Ok((false, format!("Invalid image: {}", e), None))
        }
    }
    
    fn get_image_info_internal(&self, file_path: &str) -> Result<(u32, u32, String, u64), Box<dyn std::error::Error>> {
        let metadata = std::fs::metadata(file_path)?;
        let img = image::open(file_path)?;
        let (width, height) = img.dimensions();
        let format = image::guess_format(&std::fs::read(file_path)?)?;
        let format_str = format!("{:?}", format).to_lowercase();
        
        Ok((width, height, format_str, metadata.len()))
    }
}

/// Python module definition
#[pymodule]
fn rust_moderation(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<ModerationResult>()?;
    m.add_class::<TextModerator>()?;
    m.add_class::<ImageModerator>()?;
    Ok(())
}
