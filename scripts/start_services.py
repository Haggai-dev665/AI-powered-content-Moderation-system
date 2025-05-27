"""
Script to start all microservices
"""

import subprocess
import time
import os
import sys
import signal
import logging
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServiceManager:
    def __init__(self):
        self.processes = []
        self.services = [
            {
                "name": "API Gateway",
                "path": "api-gateway",
                "file": "main.py",
                "port": 8000
            },
            {
                "name": "Text Moderation Service",
                "path": "text-moderation-service",
                "file": "main.py",
                "port": 8001
            },
            {
                "name": "Image Moderation Service",
                "path": "image-moderation-service",
                "file": "main.py",
                "port": 8002
            }
        ]
    
    def start_service(self, service):
        """Start a single service"""
        try:
            service_path = os.path.join(os.path.dirname(__file__), "..", service["path"])
            
            logger.info(f"Starting {service['name']} on port {service['port']}...")
            
            # Change to service directory and start
            process = subprocess.Popen(
                [sys.executable, service["file"]],
                cwd=service_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes.append({
                "process": process,
                "name": service["name"],
                "port": service["port"]
            })
            
            logger.info(f"{service['name']} started with PID {process.pid}")
            return process
            
        except Exception as e:
            logger.error(f"Failed to start {service['name']}: {str(e)}")
            return None
    
    def start_all_services(self):
        """Start all services"""
        logger.info("Starting all content moderation services...")
        
        # Start services with delays to avoid port conflicts
        for i, service in enumerate(self.services):
            self.start_service(service)
            if i < len(self.services) - 1:  # Don't wait after the last service
                time.sleep(2)  # Wait 2 seconds between service starts
        
        logger.info("All services started!")
        self.print_service_info()
    
    def print_service_info(self):
        """Print information about running services"""
        print("\n" + "="*60)
        print("🚀 AI Content Moderation System - Services Running")
        print("="*60)
        
        for proc_info in self.processes:
            if proc_info["process"].poll() is None:  # Process is still running
                print(f"✅ {proc_info['name']}: http://localhost:{proc_info['port']}")
            else:
                print(f"❌ {proc_info['name']}: Failed to start")
        
        print("\n📖 API Documentation:")
        print("   • API Gateway: http://localhost:8000/docs")
        print("   • Text Service: http://localhost:8001/docs")
        print("   • Image Service: http://localhost:8002/docs")
        
        print("\n🔍 Health Checks:")
        print("   • Overall Health: http://localhost:8000/health")
        print("   • Service Status: http://localhost:8000/api/v1/services/status")
        
        print("\n💡 Example Usage:")
        print("   • Text Moderation: POST http://localhost:8000/api/v1/moderate/text")
        print("   • Image Moderation: POST http://localhost:8000/api/v1/moderate/image")
        
        print("\n⚠️  Press Ctrl+C to stop all services")
        print("="*60)
    
    def stop_all_services(self):
        """Stop all services"""
        logger.info("Stopping all services...")
        
        for proc_info in self.processes:
            try:
                if proc_info["process"].poll() is None:  # Process is still running
                    logger.info(f"Stopping {proc_info['name']}...")
                    proc_info["process"].terminate()
                    
                    # Wait up to 5 seconds for graceful shutdown
                    try:
                        proc_info["process"].wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        logger.warning(f"Force killing {proc_info['name']}...")
                        proc_info["process"].kill()
                        proc_info["process"].wait()
                    
                    logger.info(f"{proc_info['name']} stopped")
                    
            except Exception as e:
                logger.error(f"Error stopping {proc_info['name']}: {str(e)}")
        
        logger.info("All services stopped")
    
    def wait_for_services(self):
        """Wait for services and handle shutdown"""
        try:
            # Wait for all processes
            while True:
                running_count = 0
                for proc_info in self.processes:
                    if proc_info["process"].poll() is None:
                        running_count += 1
                    else:
                        # Process has stopped
                        logger.warning(f"{proc_info['name']} has stopped unexpectedly")
                
                if running_count == 0:
                    logger.info("All services have stopped")
                    break
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Received shutdown signal...")
            self.stop_all_services()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal")
    sys.exit(0)

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import transformers
        logger.info("All required dependencies found")
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {str(e)}")
        logger.error("Please run: pip install -r requirements.txt")
        return False

def main():
    """Main function"""
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Start services
    manager = ServiceManager()
    
    try:
        manager.start_all_services()
        manager.wait_for_services()
    except KeyboardInterrupt:
        pass
    finally:
        manager.stop_all_services()

if __name__ == "__main__":
    main()
