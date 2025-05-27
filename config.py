"""
Configuration management for the AI Content Moderation System
Handles environment variables and settings for all services
"""

import os
import logging
from typing import Optional
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Config:
    """Configuration class for the moderation system"""
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///moderation.db")
    DATABASE_ECHO: bool = os.getenv("DATABASE_ECHO", "false").lower() == "true"
    
    # Service Hosts and Ports
    TEXT_SERVICE_HOST: str = os.getenv("TEXT_SERVICE_HOST", "localhost")
    TEXT_SERVICE_PORT: int = int(os.getenv("TEXT_SERVICE_PORT", "8001"))
    TEXT_SERVICE_WORKERS: int = int(os.getenv("TEXT_SERVICE_WORKERS", "1"))
    
    IMAGE_SERVICE_HOST: str = os.getenv("IMAGE_SERVICE_HOST", "localhost")
    IMAGE_SERVICE_PORT: int = int(os.getenv("IMAGE_SERVICE_PORT", "8002"))
    IMAGE_SERVICE_WORKERS: int = int(os.getenv("IMAGE_SERVICE_WORKERS", "1"))
    
    GATEWAY_HOST: str = os.getenv("GATEWAY_HOST", "localhost")
    GATEWAY_PORT: int = int(os.getenv("GATEWAY_PORT", "8000"))
    GATEWAY_WORKERS: int = int(os.getenv("GATEWAY_WORKERS", "1"))
    
    # Model Configuration
    HUGGINGFACE_CACHE_DIR: str = os.getenv("HUGGINGFACE_CACHE_DIR", "./models/cache")
    DOWNLOAD_MODELS_ON_STARTUP: bool = os.getenv("DOWNLOAD_MODELS_ON_STARTUP", "true").lower() == "true"
    
    # Text Moderation Models
    TOXICITY_MODEL: str = os.getenv("TOXICITY_MODEL", "martin-ha/toxic-comment-model")
    HATE_SPEECH_MODEL: str = os.getenv("HATE_SPEECH_MODEL", "unitary/toxic-bert")
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # Security
    API_KEY: Optional[str] = os.getenv("API_KEY")
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    
    # Image Processing
    MAX_IMAGE_SIZE_MB: int = int(os.getenv("MAX_IMAGE_SIZE_MB", "10"))
    MAX_IMAGE_DIMENSION: int = int(os.getenv("MAX_IMAGE_DIMENSION", "4096"))
    SUPPORTED_IMAGE_FORMATS: str = os.getenv("SUPPORTED_IMAGE_FORMATS", "jpg,jpeg,png,webp")
    
    # Performance
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "32"))
    MAX_CONCURRENT_REQUESTS: int = int(os.getenv("MAX_CONCURRENT_REQUESTS", "10"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    
    # Development
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    RELOAD: bool = os.getenv("RELOAD", "false").lower() == "true"
    
    @classmethod
    def load_env_file(cls, env_path: str = ".env"):
        """Load environment variables from a .env file"""
        env_file = Path(env_path)
        if env_file.exists():
            logger.info(f"Loading environment variables from {env_path}")
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
        else:
            logger.warning(f"Environment file {env_path} not found")
    
    @classmethod
    def setup_logging(cls):
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, cls.LOG_LEVEL.upper()),
            format=cls.LOG_FORMAT
        )
    
    @classmethod
    def get_service_url(cls, service: str) -> str:
        """Get the full URL for a service"""
        if service == "text":
            return f"http://{cls.TEXT_SERVICE_HOST}:{cls.TEXT_SERVICE_PORT}"
        elif service == "image":
            return f"http://{cls.IMAGE_SERVICE_HOST}:{cls.IMAGE_SERVICE_PORT}"
        elif service == "gateway":
            return f"http://{cls.GATEWAY_HOST}:{cls.GATEWAY_PORT}"
        else:
            raise ValueError(f"Unknown service: {service}")
    
    @classmethod
    def validate_config(cls):
        """Validate the configuration"""
        issues = []
        
        # Check if cache directory is writable
        cache_dir = Path(cls.HUGGINGFACE_CACHE_DIR)
        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            issues.append(f"Cannot create cache directory {cache_dir}: {e}")
        
        # Validate image formats
        valid_formats = {'jpg', 'jpeg', 'png', 'webp', 'gif', 'bmp'}
        configured_formats = set(cls.SUPPORTED_IMAGE_FORMATS.lower().split(','))
        invalid_formats = configured_formats - valid_formats
        if invalid_formats:
            issues.append(f"Invalid image formats: {invalid_formats}")
        
        # Check port availability (basic validation)
        ports = [cls.TEXT_SERVICE_PORT, cls.IMAGE_SERVICE_PORT, cls.GATEWAY_PORT]
        unique_ports = set(ports)
        if len(unique_ports) != len(ports):
            issues.append("Service ports must be unique")
        
        if issues:
            logger.error("Configuration validation failed:")
            for issue in issues:
                logger.error(f"  - {issue}")
            return False
        
        logger.info("Configuration validation passed")
        return True

# Initialize configuration
config = Config()

# Load .env file if it exists
config.load_env_file()

# Setup logging
config.setup_logging()
