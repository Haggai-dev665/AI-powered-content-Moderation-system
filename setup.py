"""
Setup script for AI Content Moderation System
Handles installation, model downloads, and system initialization
"""

import subprocess
import sys
import os
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_command(command, description, shell=True):
    """Run a command and handle errors"""
    logger.info(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=shell, check=True, capture_output=True, text=True)
        logger.info(f"✓ {description} completed successfully")
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ {description} failed:")
        logger.error(f"Command: {command}")
        logger.error(f"Exit code: {e.returncode}")
        logger.error(f"STDOUT: {e.stdout}")
        logger.error(f"STDERR: {e.stderr}")
        return None

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        logger.error(f"Python 3.8+ required, found {version.major}.{version.minor}")
        return False
    logger.info(f"✓ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def install_dependencies():
    """Install Python dependencies"""
    logger.info("Installing Python dependencies...")
    
    # Upgrade pip first
    run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                "Upgrading pip", shell=False)
    
    # Install requirements
    requirements_file = Path("requirements.txt")
    if requirements_file.exists():
        result = run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                           "Installing requirements", shell=False)
        if result is None:
            logger.error("Failed to install dependencies")
            return False
    else:
        logger.error("requirements.txt not found")
        return False
    
    return True

def create_directories():
    """Create necessary directories"""
    directories = [
        "models/cache",
        "logs",
        "data",
        "temp"
    ]
    
    for directory in directories:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"✓ Created directory: {directory}")

def setup_environment():
    """Setup environment configuration"""
    env_template = Path(".env.template")
    env_file = Path(".env")
    
    if env_template.exists() and not env_file.exists():
        logger.info("Creating .env file from template...")
        with open(env_template, 'r') as template:
            content = template.read()
        
        with open(env_file, 'w') as env:
            env.write(content)
        
        logger.info("✓ Created .env file from template")
        logger.info("📝 Please edit .env file to configure your settings")
    elif env_file.exists():
        logger.info("✓ .env file already exists")
    else:
        logger.warning("⚠️  No .env.template found, skipping environment setup")

def download_models():
    """Download AI models"""
    logger.info("Downloading AI models...")
    
    download_script = Path("scripts/download_models.py")
    if download_script.exists():
        result = run_command([sys.executable, str(download_script)], 
                           "Downloading AI models", shell=False)
        if result is None:
            logger.warning("⚠️  Model download failed, models will be downloaded on first use")
        else:
            logger.info("✓ Models downloaded successfully")
    else:
        logger.warning("⚠️  Download script not found, models will be downloaded on first use")

def initialize_database():
    """Initialize the database"""
    logger.info("Initializing database...")
    
    try:
        # Import and run database initialization
        sys.path.append(str(Path.cwd()))
        from database.db import init_db
        
        init_db()
        logger.info("✓ Database initialized successfully")
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
        return False
    
    return True

def run_tests():
    """Run basic tests to verify setup"""
    logger.info("Running basic tests...")
    
    # Check if pytest is available
    try:
        import pytest
        result = run_command([sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"], 
                           "Running tests", shell=False)
        if result:
            logger.info("✓ All tests passed")
        else:
            logger.warning("⚠️  Some tests failed, but setup can continue")
    except ImportError:
        logger.warning("⚠️  pytest not available, skipping tests")

def main():
    """Main setup function"""
    logger.info("🚀 Starting AI Content Moderation System Setup")
    logger.info("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Setup environment
    setup_environment()
    
    # Install dependencies
    if not install_dependencies():
        logger.error("Setup failed during dependency installation")
        sys.exit(1)
    
    # Download models (optional)
    download_models()
    
    # Initialize database
    if not initialize_database():
        logger.error("Setup failed during database initialization")
        sys.exit(1)
    
    # Run tests (optional)
    run_tests()
    
    logger.info("=" * 50)
    logger.info("🎉 Setup completed successfully!")
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Review and edit the .env file with your configuration")
    logger.info("2. Start the services with: python scripts/start_services.py")
    logger.info("3. Access the API gateway at: http://localhost:8000")
    logger.info("4. View API documentation at: http://localhost:8000/docs")
    logger.info("")
    logger.info("For more information, see docs/README.md")

if __name__ == "__main__":
    main()
